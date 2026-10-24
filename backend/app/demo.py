from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import get_db
from .auth import current_user
from .models import Account, Relationship, User
from .schemas import WEIGHTS
router=APIRouter()
@router.post('/demo/load',status_code=201)
def load_demo(db: Session=Depends(get_db), user: User=Depends(current_user)):
    # Lock the user row on PostgreSQL so concurrent seed requests cannot duplicate data.
    db.scalar(select(User).where(User.id==user.id).with_for_update())
    if db.scalar(select(Account).where(Account.user_id==user.id).limit(1)):
        raise HTTPException(409,'Demo data can only be loaded into an empty profile.')
    data=[('Gmail','Email','Critical',False,False),('Apple ID','Other','Critical',True,True),
          ('Amazon','Shopping','Medium',False,False),('Instagram','Social Media','Medium',False,False),
          ('PayPal','Financial','Critical',False,False),('Dropbox','Cloud Storage','High',True,False),
          ('Steam','Gaming','Low',True,False),('Discord','Communication','Medium',False,False),
          ('LinkedIn','Work','Medium',True,False),('Password Manager','Password Manager','Critical',True,False)]
    accounts={}
    for name,category,importance,mfa,passkey in data:
        a=Account(user_id=user.id,service_name=name,category=category,importance=importance,has_mfa=mfa,has_passkey=passkey,mfa_type='Authenticator' if mfa else 'None',email_or_username='alex@example.com',notes='Fictional demo account')
        db.add(a);db.flush();accounts[name]=a
    links=[('Gmail','Amazon','PASSWORD_RESET'),('Gmail','Instagram','RECOVERY_EMAIL'),('Gmail','Dropbox','PASSWORD_RESET'),
           ('Gmail','LinkedIn','PASSWORD_RESET'),('Gmail','Discord','SIGN_IN_WITH_GOOGLE'),('Gmail','PayPal','PASSWORD_RESET'),
           ('Gmail','Apple ID','RECOVERY_EMAIL'),('Apple ID','Gmail','RECOVERY_EMAIL'),('Apple ID','Password Manager','RECOVERY_EMAIL'),
           ('Password Manager','Amazon','PASSWORD_MANAGER_STORES_CREDENTIAL'),('Password Manager','PayPal','PASSWORD_MANAGER_STORES_CREDENTIAL'),
           ('Discord','Steam','SHARED_PASSWORD')]
    for source,target,kind in links:
        db.add(Relationship(source_account_id=accounts[source].id,target_account_id=accounts[target].id,relationship_type=kind,risk_weight=WEIGHTS[kind],notes='Demo dependency; not a claim about service behavior.'))
    db.commit()
    return {'accounts':len(accounts),'relationships':len(links)}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, or_, func
from sqlalchemy.exc import IntegrityError
from .db import get_db
from .auth import current_user
from .models import Account, Relationship, User
from .schemas import AccountInput, AccountOutput, RelationshipInput, RelationshipOutput, WEIGHTS
router = APIRouter()
def owned(db, user, account_id):
    account = db.scalar(select(Account).where(Account.id==account_id, Account.user_id==user.id))
    if not account: raise HTTPException(404, "Account not found")
    return account
def profile(db, user):
    accounts = list(db.scalars(select(Account).where(Account.user_id==user.id).order_by(Account.created_at)))
    ids = [a.id for a in accounts]
    relationships = list(db.scalars(select(Relationship).where(Relationship.source_account_id.in_(ids), Relationship.target_account_id.in_(ids)).order_by(Relationship.id)))
    return accounts, relationships
@router.get("/accounts", response_model=list[AccountOutput])
def accounts(db: Session=Depends(get_db), user: User=Depends(current_user)):
    return profile(db,user)[0]
@router.post("/accounts", response_model=AccountOutput, status_code=201)
def create_account(data: AccountInput, db: Session=Depends(get_db), user: User=Depends(current_user)):
    if db.scalar(select(func.count()).select_from(Account).where(Account.user_id==user.id)) >= 100:
        raise HTTPException(422,"MVP profiles support up to 100 accounts.")
    account = Account(user_id=user.id, **data.model_dump()); db.add(account); db.commit(); db.refresh(account)
    return account
@router.put("/accounts/{account_id}", response_model=AccountOutput)
def update_account(account_id: str, data: AccountInput, db: Session=Depends(get_db), user: User=Depends(current_user)):
    account=owned(db,user,account_id)
    for k,v in data.model_dump().items(): setattr(account,k,v)
    db.commit(); db.refresh(account); return account
@router.delete("/accounts/{account_id}", status_code=204)
def delete_account(account_id: str, db: Session=Depends(get_db), user: User=Depends(current_user)):
    account=owned(db,user,account_id)
    db.execute(delete(Relationship).where(or_(Relationship.source_account_id==account_id,Relationship.target_account_id==account_id)))
    db.delete(account); db.commit()
@router.get("/relationships", response_model=list[RelationshipOutput])
def relationships(db: Session=Depends(get_db), user: User=Depends(current_user)): return profile(db,user)[1]
@router.post("/relationships", response_model=RelationshipOutput, status_code=201)
def create_relationship(data: RelationshipInput, db: Session=Depends(get_db), user: User=Depends(current_user)):
    owned(db,user,data.source_account_id); owned(db,user,data.target_account_id)
    if data.source_account_id==data.target_account_id: raise HTTPException(422,"Choose two different accounts.")
    if len(profile(db,user)[1]) >= 500: raise HTTPException(422,"MVP profiles support up to 500 connections.")
    values=data.model_dump(); values['risk_weight']=data.risk_weight if data.risk_weight is not None else WEIGHTS[data.relationship_type]
    relation=Relationship(**values); db.add(relation)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409,"This connection already exists.")
    db.refresh(relation); return relation
@router.delete("/relationships/{relationship_id}", status_code=204)
def delete_relationship(relationship_id: str, db: Session=Depends(get_db), user: User=Depends(current_user)):
    relation=db.get(Relationship,relationship_id)
    if not relation: raise HTTPException(404,"Connection not found")
    owned(db,user,relation.source_account_id); owned(db,user,relation.target_account_id)
    db.delete(relation); db.commit()

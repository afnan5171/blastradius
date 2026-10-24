def add(client, name="Gmail"):
    result=client.post("/accounts",json={"service_name":name,"category":"Email"})
    assert result.status_code==201
    return result.json()
def test_crud(client):
    a=add(client); b=add(client,"Amazon")
    r=client.post("/relationships",json={"source_account_id":a["id"],"target_account_id":b["id"],"relationship_type":"PASSWORD_RESET"})
    assert r.status_code==201 and r.json()["risk_weight"]==10
    assert client.post("/relationships",json={k:v for k,v in r.json().items() if k!='id'}).status_code==409
    assert client.put('/accounts/'+a['id'],json={"service_name":"Updated","has_mfa":True}).json()['has_mfa']
    assert client.delete('/accounts/'+a['id']).status_code==204
    assert client.get('/relationships').json()==[]
    assert len(client.get('/accounts').json())==1
def test_ownership(client):
    a=add(client)
    client.cookies.clear()
    assert client.get('/accounts').status_code==401
    client.post('/auth/demo')
    b=add(client,'Other')
    assert client.get('/accounts').json()[0]['id']==b['id']
    assert client.put('/accounts/'+a['id'],json={"service_name":"Attack"}).status_code==404
    assert client.post('/relationships',json={"source_account_id":b['id'],"target_account_id":a['id'],"relationship_type":"OTHER"}).status_code==404
def test_validation(client):
    assert client.post('/accounts',json={"service_name":"  "}).status_code==422
    assert client.post('/accounts',json={"service_name":"Test","password":"secret"}).status_code==422
    a=add(client)
    assert client.post('/relationships',json={"source_account_id":a['id'],"target_account_id":a['id'],"relationship_type":"OTHER"}).status_code==422
    assert client.post('/auth/demo',headers={"Sec-Fetch-Site":"cross-site"}).status_code==403
def test_simulation(client):
    a=add(client); b=add(client,'PayPal')
    client.post('/relationships',json={"source_account_id":a['id'],"target_account_id":b['id'],"relationship_type":"PASSWORD_RESET"})
    result=client.post('/simulate/'+a['id']).json()
    assert result['affected_count']==1
    assert result['paths'][0]['relationship_types']==['PASSWORD_RESET']
    client.cookies.clear();client.post('/auth/demo')
    assert client.post('/simulate/'+a['id']).status_code==404

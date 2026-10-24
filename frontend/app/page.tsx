'use client';
import {useEffect,useState} from 'react';
import IdentityMap from '@/components/IdentityMap';
import {api,Account,Connection} from '@/lib/types';
export default function Page(){const [accounts,setAccounts]=useState<Account[]>([]);const [connections,setConnections]=useState<Connection[]>([]);const [selected,setSelected]=useState<string|null>(null);const [error,setError]=useState('');useEffect(()=>{(async()=>{await api('/auth/demo','POST');setAccounts(await api('/accounts'));setConnections(await api('/relationships'));})().catch(e=>setError(e.message));},[]);return <main><h1>BlastRadius</h1><p>Your digital life, connected.</p>{error&&<p role="alert">{error}</p>}<div style={{height:600}}><IdentityMap accounts={accounts} connections={connections} selected={selected} onSelect={setSelected} simulation={null}/></div></main>}

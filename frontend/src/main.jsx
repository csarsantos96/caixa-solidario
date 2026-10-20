import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Heart} from 'lucide-react';
import App from './App.jsx';
import {apiFetch} from './api.js';
import './styles.css';

function Root() {
  const [user,setUser]=useState(null),[ready,setReady]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  useEffect(()=>{
    let alive=true;
    apiFetch('/api/session').then(async r=>{if(r.ok&&alive)setUser(await r.json());}).catch(()=>{if(alive)setError('Não foi possível conectar ao servidor. Confira se o backend está funcionando.');}).finally(()=>{if(alive)setReady(true);});
    const expired=()=>setUser(null);
    const logout=async()=>{try{const r=await apiFetch('/api/logout',{method:'POST'});if(!r.ok)throw Error();setUser(null);}catch{alert('Não foi possível sair. Confira a conexão e tente novamente.');}};
    window.addEventListener('auth-expired',expired);window.addEventListener('request-logout',logout);
    return()=>{alive=false;window.removeEventListener('auth-expired',expired);window.removeEventListener('request-logout',logout);};
  },[]);
  async function login(e){e.preventDefault();setBusy(true);setError('');const form=new FormData(e.currentTarget);try{const r=await apiFetch('/api/login',{method:'POST',body:JSON.stringify({username:form.get('username'),password:form.get('password')})});const data=await r.json();if(!r.ok)throw Error(data.error||'Não foi possível entrar.');setUser(data);}catch(e){setError(e.message||'Falha na conexão.');}finally{setBusy(false);}}
  if(!ready)return <div className="login-page">Conectando ao caixa…</div>;
  if(user)return <App/>;
  return <main className="login-page"><form className="login-card" onSubmit={login}><div className="login-brand"><Heart size={30}/> Caixa Solidário</div><span className="eyebrow">ACESSO DO OPERADOR</span><h1>Seu evento, organizado.</h1><p className="muted">Entre para cadastrar alimentos e registrar as vendas.</p>{error&&<div className="alert error" role="alert">{error}</div>}<label>Usuário<input name="username" autoComplete="username" defaultValue="admin" required maxLength={100}/></label><label>Senha<input name="password" type="password" autoComplete="current-password" required maxLength={500}/></label><button className="primary full" disabled={busy}>{busy?'Entrando…':'Entrar no caixa'}</button><small className="login-help">Use os dados gerados por scripts/configure.py.</small></form></main>;
}
createRoot(document.getElementById('root')).render(<Root/>);

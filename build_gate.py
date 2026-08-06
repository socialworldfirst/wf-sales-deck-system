#!/usr/bin/env python3
"""Build the wf-gated index.html for the WF Sales Deck System spec.

Reads system_spec.html, encrypts the slide markup (AES-GCM + PBKDF2) and writes
index.html with the standard gate. The kit CSS/JS stay unencrypted; the deck
runtime is loaded dynamically after unlock so it initialises against the
injected slides.
"""
import os, re, json, base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes

HERE = os.path.dirname(os.path.abspath(__file__))
PASSWORD = "wf"          # internal team
ITERATIONS = 100_000
LS_KEY = "wfsalesdeck_pw"


def encrypt_payload(plaintext, password=PASSWORD):
    salt, iv = os.urandom(16), os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
    key = kdf.derive(password.encode("utf-8"))
    ct = AESGCM(key).encrypt(iv, plaintext.encode("utf-8"), None)
    return {
        "v": 1,
        "salt": base64.b64encode(salt).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "iterations": ITERATIONS,
        "ciphertext": base64.b64encode(ct).decode("ascii"),
    }


src = open(os.path.join(HERE, "system_spec.html"), encoding="utf-8").read()
body = re.search(r"<body>(.*)</body>", src, re.S).group(1)
body = body.replace('<script src="kit/sales_deck.js"></script>', "").strip()

payload = json.dumps(encrypt_payload(body))

html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>WF Sales Deck System</title>
<link rel="stylesheet" href="kit/sales_deck.css">
<style>
  body.locked{overflow:hidden}
  #gate{position:fixed;inset:0;z-index:999;display:flex;align-items:center;justify-content:center;
    background:linear-gradient(128deg,#32006E 0%,#23054E 46%,#13002D 100%)}
  #gate-card{text-align:center;padding:6vh 4vw}
  #gate-card h2{font-family:'Poppins',sans-serif;font-weight:500;font-size:clamp(26px,3vw,54px);
    color:#fff;letter-spacing:-.01em}
  #gate-card h2 span{color:#FF0051}
  #gate-card p{font-family:'Poppins',sans-serif;font-weight:400;font-size:14px;
    color:rgba(255,255,255,.6);margin-top:1.4vh}
  #gate-form{margin-top:4vh;display:flex;gap:10px;justify-content:center}
  #gate-input{font-family:'Poppins',sans-serif;font-size:15px;padding:.85em 1.3em;border-radius:999px;
    border:1px solid rgba(221,192,255,.35);background:rgba(255,255,255,.07);color:#fff;outline:none;width:230px}
  #gate-input::placeholder{color:rgba(255,255,255,.4)}
  #gate-input:focus{border-color:#FF0051}
  #gate-btn{font-family:'Poppins',sans-serif;font-weight:500;font-size:15px;padding:.85em 1.9em;
    border-radius:999px;border:none;background:#FF0051;color:#fff;cursor:pointer}
  #gate-err{font-family:'Poppins',sans-serif;font-size:13px;color:#FFACC6;margin-top:2vh;min-height:1em}
  #lockdev{position:fixed;right:14px;bottom:12px;z-index:99;font-family:'Poppins',sans-serif;
    font-size:11px;color:rgba(255,255,255,.35);text-decoration:none}
  #lockdev:hover{color:#FF0051}
</style>
</head>
<body class="locked">
<div id="gate">
  <div id="gate-card">
    <h2>WF <span>Sales Deck System</span></h2>
    <p>Internal. Extracted from the 2026 WorldFirst Sales Deck.</p>
    <form id="gate-form" onsubmit="return gateSubmit(event)">
      <input id="gate-input" type="password" placeholder="password" autocomplete="off" autofocus>
      <button id="gate-btn" type="submit">Enter</button>
    </form>
    <div id="gate-err"></div>
  </div>
</div>
<div id="deck" hidden></div>
<a id="lockdev" href="#" hidden onclick="localStorage.removeItem('__LS__');location.reload();return false;">lock device</a>
<script type="application/json" id="cipher">__PAYLOAD__</script>
<script>
function b64ToBytes(b64){const bin=atob(b64),b=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++)b[i]=bin.charCodeAt(i);return b}
async function deriveKey(pw,salt,iterations){const enc=new TextEncoder();
  const base=await crypto.subtle.importKey("raw",enc.encode(pw),"PBKDF2",false,["deriveKey"]);
  return crypto.subtle.deriveKey({name:"PBKDF2",salt,iterations,hash:"SHA-256"},base,
    {name:"AES-GCM",length:256},false,["decrypt"])}
async function decryptPayload(pw){
  const blob=JSON.parse(document.getElementById('cipher').textContent);
  const key=await deriveKey(pw,b64ToBytes(blob.salt),blob.iterations);
  const plain=await crypto.subtle.decrypt({name:"AES-GCM",iv:b64ToBytes(blob.iv)},key,b64ToBytes(blob.ciphertext));
  return new TextDecoder().decode(plain)}
function reveal(html){
  const d=document.getElementById('deck');
  d.innerHTML=html; d.hidden=false;
  document.getElementById('gate').style.display='none';
  document.getElementById('lockdev').hidden=false;
  document.body.classList.remove('locked');
  const s=document.createElement('script'); s.src='kit/sales_deck.js'; document.body.appendChild(s);
}
async function gateSubmit(e){
  e.preventDefault();
  const inp=document.getElementById('gate-input'), err=document.getElementById('gate-err');
  err.textContent='';
  try{
    const html=await decryptPayload(inp.value);
    reveal(html);
    try{localStorage.setItem('__LS__',inp.value)}catch(_){}
  }catch(ex){err.textContent='wrong password';inp.value='';inp.focus()}
  return false}
(async()=>{try{const c=localStorage.getItem('__LS__');
  if(c){reveal(await decryptPayload(c))}}catch(_){try{localStorage.removeItem('__LS__')}catch(_){}}})();
</script>
</body>
</html>
"""

html = html.replace("__PAYLOAD__", payload).replace("__LS__", LS_KEY)
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
print(f"index.html written ({len(html)//1024} KB), password '{PASSWORD}'")

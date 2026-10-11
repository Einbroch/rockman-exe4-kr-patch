"""Require an adopted decoder and producer contract before short-text compilation."""
import json
from analyze_project import sha

def check_selection(contract,key,source,wording,table):
    if contract['schema']!=1 or contract['profiles'][key]['source_sha256']!=sha(source):
        raise ValueError('consumer contract source identity drift')
    for anchor in contract['profiles'][key]['anchors']:
        at,size=anchor['offset'],anchor['size']
        if sha(source[at:at+size])!=anchor['sha256']:
            raise ValueError('consumer contract native anchor drift')
    approved={x['id']:x for x in contract['supported_entries']}
    for entry in wording['entries']:
        if entry.get('revision',key)!=key:continue
        c=approved.get(entry['id'])
        if c is None:raise ValueError('unclassified short-text consumer: '+entry['id'])
        if entry['source']!=c['source']:raise ValueError('consumer contract source wording drift')
        # A list is a command-bearing script's literals; the budget covers them all.
        text=''.join(entry['text']) if isinstance(entry['text'],list) else entry['text']
        if len(text)>c['max_cells']:raise ValueError('consumer cell budget exceeded')
        encoded=bytearray();rest=text
        while rest:
            # Bracketed table tokens ([MB], [z]) are one code each.
            close=rest.find(']')+1 if rest[0]=='[' else 0
            ch=rest[:close] if close and rest[:close] in table else rest[0]
            if ch=='\n':encoded+=b'\xe8'
            elif len(ch)==1 and 0xac00<=ord(ch)<=0xd7a3:encoded+=b'\xf9\xfc'+(ord(ch)-0xac00).to_bytes(2,'little')
            elif ch in table:encoded+=table[ch]
            else:raise ValueError('consumer has unencodable literal: '+ch)
            rest=rest[len(ch):]
        encoded+=b'\xe5'
        if c.get('max_encoded_bytes') is not None and len(encoded)>c['max_encoded_bytes']:
            raise ValueError('consumer encoded buffer budget exceeded')
    return True

def validate_selection(p,key,source,wording):
    path=p/'tools/specs/exe4_consumer_contracts_v1.json'
    contract=json.loads(path.read_text(encoding='utf-8'));table={}
    for line in (p/'external/textpet-plugins/exe4-utf8.tbl').read_text(encoding='utf-8-sig').splitlines():
        code,sep,text=line.partition('=')
        if sep and (len(text)==1 or text[:1]=='['):table.setdefault(text,bytes.fromhex(code))
    check_selection(contract,key,source,wording,table)
    return {'consumer_contract_sha256':sha(path.read_bytes()),'consumer_selection_verified':True}

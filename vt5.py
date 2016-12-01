#!/usr/bin/python
# -*- coding: utf-8 -*-
# Videovuokraamon käyttöliittymän palvelinpuolen ohjelmakoodi
# tiea218 viikkotehtävä 5
# Author: Toni Pikkarainen
# Date: 1.11.2016

from functools import wraps
from flask import Flask, session, redirect, url_for, escape, request, Response, render_template, make_response
import sqlite3
import hashlib
import logging
import os
import json
import datetime
import time
import sys

logging.basicConfig(filename=os.path.abspath('../../hidden/vt5/flask.log'),level=logging.DEBUG)
app = Flask(__name__) 
app.debug = True
app.secret_key = '7wZ]\x89\xc3z\xb8\x97\xba|\x95\xa2x\xf6lP\xaas\xbf\xe7\x93\xf32'


# Tarkastaa voiko poistaa elokuvan
# eli liittyykö elokuvaan vuokrauksia.
# Palauttaa true jos voi poistaa.    
def voikoPoistaaElokuvan(eid,cur):
    sql="""
    SELECT VuokrausPVM 
    FROM Vuokraus
    WHERE ElokuvaID=:eid
    """
    paivat=[]
    try:
        cur.execute(sql, {"eid":eid})
    except:
        logging.debug("virhe")
        logging.debug(sys.exc_info()[0])
    
    for row in cur.fetchall():
        paivat.append(dict(vpvm=row['VuokrausPVM'].decode("UTF-8")))
       
    return not paivat

    
# Tarkastaa voiko poistaa jäsenen
# eli liittyykö jäseneen vuokrauksia.
# Palauttaa true jos voi poistaa. 
def voikoPoistaaJasenen(jid,cur):
    sql="""
    SELECT VuokrausPVM 
    FROM Vuokraus
    WHERE JasenID=:jid
    """
    paivat=[]
    try:
        cur.execute(sql, {"jid":jid})
    except:
        logging.debug("virhe")
        logging.debug(sys.exc_info()[0])
    
    for row in cur.fetchall():
        paivat.append(dict(vpvm=row['VuokrausPVM'].decode("UTF-8")))
       
    return not paivat    
    
# Luo yhteyden tietokantaan.
def connect():
    try:
        con = sqlite3.connect(os.path.abspath('../../hidden/vt5/video'))
        con.row_factory = sqlite3.Row
        con.text_factory = str
    except Exception as e:
        logging.debug("Kanta ei aukea")
        # sqliten antama virheilmoitus:
        logging.debug(str(e))
    return con
    
# Suorittaa kyselyn kursorilla   
def teeKysely(sql, virheTeksti, cur):
    try:
        cur.execute(sql)
    except Exception as e:
        logging.debug(virheTeksti)
        logging.debug(str(e))
        
# Tarkastaa päivämäärän oikeellisuuden.
# Ei hyväksy vanhempia päiviä kuin nykypäivä.
def validoiPvm(text):
    try:
        if datetime.datetime.strptime(text, '%Y-%m-%d') < datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            return False
    except: 
        return False
        
    try:
        return text == datetime.datetime.strptime(text, '%Y-%m-%d').strftime('%Y-%m-%d')
    except:
        return False

# Tarkastaa päivämäärän oikeellisuuden.       
def validoiPvm_muok(text):
    try:
        return text == datetime.datetime.strptime(text, '%Y-%m-%d').strftime('%Y-%m-%d')
    except:
        return False

# Hakee jäsenet kannasta
@app.route('/hae_jasenet', methods=['GET']) 
def hae_jasenet():
    con = connect()
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
    
    cur = con.cursor()
    
    sql="""
    SELECT Nimi, JasenID
    FROM Jasen
    """
    jasenet = []
    
    try:
        cur.execute(sql)
    except Exception as e:
        logging.debug("ei löydy jäseniä")
        logging.debug(str(e))
    
    for row in cur.fetchall():
        jasenet.append(dict(jasen=row['Nimi'].decode("utf-8"), jid=row['JasenID']))
   
    con.close()
    
    resp = make_response( render_template("jasenet.xml",jasenet=jasenet, kirjaus=kirjaus))
    resp.charset = "UTF-8"
    resp.mimetype = "text/xml"
    return resp
    
# Hakee elokuvat kannasta
@app.route('/hae_elokuvat', methods=['GET'])     
def hae_elokuvat():
    con = connect()
    
    cur = con.cursor()
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
    
    sql = """
    SELECT Nimi, ElokuvaID
    FROM Elokuva
    """
    elokuvat = []
    
    try:
        cur.execute(sql)
    except Exception as e:
        logging.debug("ei löydy elokuvia")
        logging.debug(str(e))
    
    for row in cur.fetchall():
        elokuvat.append(dict(elokuva=row['Nimi'].decode("utf-8"), eid=row['ElokuvaID']))
   
    con.close()
    
    resp = make_response( render_template("elokuvat.xml",elokuvat=elokuvat, kirjaus=kirjaus))
    resp.charset = "UTF-8"
    resp.mimetype = "text/xml"
    return resp

# Hakee vuokraukset kannasta
@app.route('/hae_vuokraukset', methods=['GET'])   
def hae_vuokraukset():  
    con = connect() # avataan yhteys
    cur = con.cursor() # luodaan kursori
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
   
    # Kysytään jäsenet ja niihin liittyvät vuokraukset.
    sql = """
    SELECT Jasen.nimi AS jasen,Jasen.JasenID as jid,Elokuva.Nimi AS elokuva,Elokuva.ElokuvaID as eid,Vuokraus.VuokrausPVM AS vpvm,
    Vuokraus.PalautusPVM as ppvm
    FROM Jasen 
    LEFT OUTER JOIN Elokuva
    ON Elokuva.ElokuvaID=Vuokraus.ElokuvaID 
    LEFT OUTER JOIN Vuokraus 
    ON Vuokraus.JasenID=Jasen.JasenID
    ORDER BY Jasen.nimi ASC, Vuokraus.VuokrausPVM ASC
    """
    vuokraukset=[]
    
    teeKysely(sql,"Ei löydy vuokraustietoja",cur)

    # Kysely palauttaa kaikki jäsenet.
    # Jos rivillä ei ole vuokrauspäivämäärää ei rivillä ole vuokrausta.
    # Lisätään silloin listaan pelkkä jäsen.
    for row in cur.fetchall():
        if row['vpvm']:
            vuokraukset.append(dict(elokuva=row['elokuva'].decode("UTF-8"),
            jasen=row['jasen'].decode("UTF-8"),vpvm=row['vpvm'].decode("UTF-8"),
            ppvm=row['ppvm'].decode("UTF-8"),jid=row['jid'],eid=row['eid']))
        else: 
            vuokraukset.append(dict(jasen=row['jasen'].decode("UTF-8"),jid=row['jid']))
    
    con.close() 
    resp = make_response( render_template("vuokraukset.xml",vuokraukset=vuokraukset,kirjaus=kirjaus))
    resp.charset = "UTF-8"
    resp.mimetype = "text/xml"
    return resp

# Hakee lajityypit kannasta    
@app.route('/hae_lajityypit', methods=['GET'])   
def hae_lajityypit():  
    con = connect() # avataan yhteys
    cur = con.cursor() # luodaan kursori
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
   
    
    sql = """
    SELECT Tyypinnimi as lajityyppi, LajityyppiID as lajiID
    FROM Lajityyppi
    """
    lajityypit=[]
    
    teeKysely(sql,"Ei löydy lajityyppeja",cur)

    for row in cur.fetchall():
        lajityypit.append(dict(lajityyppi=row['lajityyppi'].decode("UTF-8"),lajiID=row['lajiID']))
        
    
    con.close() 
    resp = make_response( render_template("lajityypit.xml",lajityypit=lajityypit,kirjaus=kirjaus))
    resp.charset = "UTF-8"
    resp.mimetype = "text/xml"
    return resp


# Käsittelee uuden elokuvan lisäyksen.  
@app.route('/uusielokuva', methods=['POST','GET']) 
def uusielokuva():
    con=connect()
    cur = con.cursor()
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
   
    virhe=""
    
    tayttoVirhe=False
    
    try:
        submit=request.form.get('lisaa_elokuva').decode("UTF-8")
    except:
        submit=""
    
    try:
        lajityyppiID=int(request.form.get('lajityyppi'))
    except:
        lajityyppiID=0
        
    try: 
        nimi=request.form.get('elokuvannimi') 
    except:
        logging.debug("ei mennyt nimi")
        logging.debug(sys.exc_info()[0])
        nimi=""
        
        
    try: 
        julkaisuvuosi=int(request.form.get('julkaisuvuosi').decode("utf-8"))
    except:
        julkaisuvuosi=""
   
    try: 
        vuokrahinta=float(request.form.get('vuokrahinta').decode("utf-8"))
    except:
        vuokrahinta=""
    
    try: 
        arvio=int(request.form.get('arvio').decode("utf-8"))
    except:
        arvio=""
    # Tarkastetaan onko kentät täytetty
    if nimi=="" or julkaisuvuosi=="" or vuokrahinta=="" or arvio=="" or kirjaus=="":
        tayttoVirhe=True
   
  
    if tayttoVirhe:
        virhe="Täytä kaikki kentät!".decode("utf-8")
   
    # Elokuvan lisääminen.
    if not tayttoVirhe:
        sql = """
        INSERT INTO elokuva (nimi,julkaisuvuosi,vuokrahinta,arvio,lajityyppiid) 
        VALUES (:nimi,:julkaisuvuosi,:vuokrahinta,:arvio,:LajityyppiID) 
        """
        try:
            cur.execute(sql, {"nimi":nimi,"julkaisuvuosi":julkaisuvuosi,"vuokrahinta":vuokrahinta, 
            "arvio":arvio,"LajityyppiID":lajityyppiID})
            con.commit()
            con.close()
            
            resp = make_response( virhe )
            resp.charset = "UTF-8"
            resp.mimetype = "text/plain"
            return resp
          
        except:
            logging.debug("ei mennyt elokuva")
            logging.debug(sys.exc_info()[0])
    
    resp = make_response( virhe )
    resp.charset = "UTF-8"
    resp.mimetype = "text/plain"
    return resp


# Käsittelee uuden jäsenen lisäyksen.  
@app.route('/uusijasen', methods=['POST','GET']) 
def uusijasen():
    con=connect()
    cur = con.cursor()
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
   
    virhe=""
    
    tayttoVirhe=False
    
    try:
        submit=request.form.get('lisaa_jasen').decode("UTF-8")
    except:
        submit=""
        
    try: 
        nimi=request.form.get('jasenennimi') 
    except:
        logging.debug("ei mennyt nimi")
        logging.debug(sys.exc_info()[0])
        nimi=""
        
        
    try: 
        osoite=request.form.get('osoite')
    except:
        osoite=""
   
    try: 
        liittymispvm=request.form.get('liittymispvm').decode("utf-8")
    except:
        liittymispvm=""
    
    try: 
        syntymavuosi=int(request.form.get('syntymavuosi').decode("utf-8"))
    except:
        syntymavuosi=""
    # Tarkastetaan onko kentät täytetty
    if nimi=="" or osoite=="" or liittymispvm=="" or syntymavuosi=="" or kirjaus=="":
        tayttoVirhe=True
   
  
    if tayttoVirhe:
        virhe="Täytä kaikki kentät!".decode("utf-8")
   
    # Jäsenen lisääminen.
    if not tayttoVirhe:
        sql = """
        INSERT INTO Jasen (nimi,osoite,liittymisPVM,syntymavuosi) 
        VALUES (:nimi,:osoite,:liittymispvm,:syntymavuosi) 
        """
        try:
            cur.execute(sql, {"nimi":nimi,"osoite":osoite,"liittymispvm":liittymispvm, 
            "syntymavuosi":syntymavuosi})
            con.commit()
            con.close()
            
            resp = make_response( virhe )
            resp.charset = "UTF-8"
            resp.mimetype = "text/plain"
            return resp
           # palataan etusivulle 
        except:
            logging.debug("ei mennyt jasen")
            logging.debug(sys.exc_info()[0])
    
    resp = make_response( virhe )
    resp.charset = "UTF-8"
    resp.mimetype = "text/plain"
    return resp

# Käsittelee elokuvan poiston
@app.route('/poista_elokuva', methods=['POST','GET'])       
def poista_elokuva():
    con=connect()
    cur = con.cursor()
    virhe=""
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
    
    try:
        elokuvaID=int(request.form.get("elokuva"))
    except:
        elokuvaID=0
        
    if voikoPoistaaElokuvan(elokuvaID,cur) and kirjaus=="ok": 
        sql = """
        DELETE FROM Elokuva WHERE ElokuvaID = :eid
        """
        try: 
            cur.execute(sql, {"eid":elokuvaID})
            con.commit()
            con.close()
            resp = make_response( virhe )
            resp.charset = "UTF-8"
            resp.mimetype = "text/plain"
            return resp
        except:
            logging.debug("Poisto ei onnistunut")
            logging.debug(sys.exc_info()[0])
    else:
        virhe="Ei voi poistaa, elokuvalla on vuokrauksia".decode("utf-8")
        
    resp = make_response( virhe )
    resp.charset = "UTF-8"
    resp.mimetype = "text/plain"
    return resp

# Käsittelee jäsenen poiston
@app.route('/poista_jasen', methods=['POST','GET'])       
def poista_jasen():
    con=connect()
    cur = con.cursor()
    virhe=""
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
    
    try:
        jasenID=int(request.form.get("jasen"))
    except:
        jasenID=0
        
    if voikoPoistaaJasenen(jasenID,cur) and kirjaus=="ok": 
        sql = """
        DELETE FROM Jasen WHERE JasenID = :jid
        """
        try: 
            cur.execute(sql, {"jid":jasenID})
            con.commit()
            con.close()
            resp = make_response( virhe )
            resp.charset = "UTF-8"
            resp.mimetype = "text/plain"
            return resp
        except:
            logging.debug("Poisto ei onnistunut")
            logging.debug(sys.exc_info()[0])
    else:
        virhe="Ei voi poistaa, jäsenellä on vuokrauksia".decode("utf-8")
        
    resp = make_response( virhe )
    resp.charset = "UTF-8"
    resp.mimetype = "text/plain"
    return resp

# Lisää uuden vuokrauksen    
@app.route('/lisaa_vuokraus', methods=['POST','GET'])      
def lisaa_vuokraus():  
    con=connect()
    cur = con.cursor()
    virhe=""
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
    
    try:
        jasenID=int(request.form.get("jasen"))
    except:
        jasenID=0
        
    try:
        elokuvaID=int(request.form.get("elokuva"))
    except:
        elokuvaID=0
        
    try:
        vuokraPvm = request.form.get('vpvm').decode("UTF-8")
    except:
        vuokraPvm = ""
        
    try:
        palautusPvm = request.form.get('ppvm')
    except:
        palautusPvm = ""
        
    if not validoiPvm(vuokraPvm):
        virhe="Päivämäärä väärässä muodossa tai kyseessä jo mennyt päivämäärä, anna muodossa VVVV-KK-PP".decode("utf-8")
    
    # Vuokrauksen lisääminen
    if validoiPvm(vuokraPvm) and kirjaus=="ok":
        sql = """
        INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
        VALUES (:jasenID,:elokuvaID,:vuokraPvm,:palautusPvm) 
        """
        try:
            cur.execute(sql, {"jasenID":jasenID,"elokuvaID":elokuvaID,"vuokraPvm":vuokraPvm, 
            "palautusPvm":palautusPvm})
            con.commit()
            con.close()
            virhe=""
            resp = make_response( virhe )
            resp.charset = "UTF-8"
            resp.mimetype = "text/plain"
            return resp
        except:
            logging.debug("ei mennyt")
            logging.debug(sys.exc_info()[0])
            virhe="Ei saatu lisättyä, hänellä on jo saman elokuvan vuokraus samalle päivälle.".decode("utf-8")
    
    con.close()
    resp = make_response( virhe )
    resp.charset = "UTF-8"
    resp.mimetype = "text/plain"
    return resp

# Päivittää tiettyä vuokrausta    
@app.route('/paivita_vuokraus', methods=['POST','GET'])      
def paivita_vuokraus():  
    con=connect()
    cur = con.cursor()
    virhe=""
    
    kirjaus=""
    
    if 'kirjautunut' in session:
        kirjaus="ok"
    
    try:
        jid=int(request.args.get("jid"))
    except:
        jid=0
        
    try:
        eid=int(request.args.get("eid"))
    except:
        eid=0
        
    try:
        vpvm=request.args.get("vpvm").decode("utf-8")
    except:
        vpvm=""
        
    try:
        ujid=int(request.args.get("ujid"))
    except:
        ujid=0
        
    try:
        ueid=int(request.args.get("ueid"))
    except:
        ueid=0
        
    try:
        uvpvm = request.args.get('uvpvm').decode("UTF-8")
    except:
        uvpvm = ""
        
    try:
        uppvm = request.args.get('uppvm')
    except:
        uppvm = ""
        
    if not validoiPvm_muok(uvpvm):
        virhe="Päivämäärä väärässä muodossa tai kyseessä jo mennyt päivämäärä, anna muodossa VVVV-KK-PP".decode("utf-8")
    
    
    # Vuokrauksen paivittaminen
    if validoiPvm_muok(uvpvm) and kirjaus=="ok":
        sql = """
        UPDATE Vuokraus SET JasenID=:ujid,ElokuvaID=:ueid,
        PalautusPVM=:uppvm,VuokrausPVM=:uvpvm
        WHERE JasenID=:jid AND ElokuvaID=:eid AND VuokrausPVM=:vpvm
        """
        
        try:
            cur.execute(sql, {"ujid":ujid,"ueid":ueid,"uppvm":uppvm, 
            "uvpvm":uvpvm, "jid":jid, "eid":eid,"vpvm":vpvm})
            con.commit()
            con.close()
            virhe=""
            resp = make_response( virhe )
            resp.charset = "UTF-8"
            resp.mimetype = "text/plain"
            return resp
        except:
            logging.debug("ei mennyt")
            logging.debug(sys.exc_info()[0])
            virhe="Ei saatu päivitettyä.".decode("utf-8")
   
    con.close()
    resp = make_response( virhe )
    resp.charset = "UTF-8"
    resp.mimetype = "text/plain"
    return resp
    
# Käsittelee kirjautumisen.    
@app.route('/kirjaudu', methods=['POST','GET']) 
def kirjaudu():
    t = hashlib.sha512()
    s = hashlib.sha512()
    
    virhe=""
    
    try:
        tunnus=request.args.get("tunnus").decode("UTF-8")
    except:
        tunnus=""
    
    
    try:
        salasana=request.args.get("salasana").decode("UTF-8")
    except:
        salasana=""
        
    try:
        submit=request.args.get('laheta_kirjaus').decode("UTF-8")
    except:
        submit=""
    
    avain = "salainenavain"
  
    
    t.update(avain)
    t.update(tunnus)
    
    s.update(avain)
    s.update(salasana)
    
    
    
    if t.digest()=="\xbb\xdfql\xf3\xf9\x1c\x11 \x0cY\x1a\x9a\x7fdn\xd1\xdb\xa3e|\xc5R\x06\xbd\x80\xd3\xff\x16\x07z\xe6\xd2F\xcb\xbaL\xf7\xa2\x19{\xc6\x8d\xb2\x92\x13\x19i\x9bj=\x95\x82fE\xf3)/q\xb1\xb6B\x9e\x1f" and \
       s.digest() == "=5Q\x0fz\x04\x98\x01/\xb7e\x80J\xfar'g\xe9\x11\xfc\xac\\W\xec%O\x9ex\x92\\s\xc8w\x87\xa5\x9e\xa9z\x9e\xd4Gh\x91s\x93\xf3)2lN\xc8\x80\xb6,\xad\x01\x1c\xc5\xddI\xcc\xda\xa8\xbb":
        
        session['kirjautunut'] = "ok"
        resp = make_response( virhe )
        resp.charset = "UTF-8"
        resp.mimetype = "text/plain"
        return resp
    
    
    
    virhe="Tarkista tunnus ja salasana!".decode("utf-8")
    resp = make_response( virhe )
    resp.charset = "UTF-8"
    resp.mimetype = "text/plain"
    return resp
        
@app.route('/etusivu', methods=['POST','GET']) 
def etusivu():
 
    return render_template('etusivu.html')
    
@app.route('/logout',methods=['POST','GET']) 
def logout():
    session.pop('kirjautunut',None)
      
    resp = make_response( "" )
    resp.charset = "UTF-8"
    resp.mimetype = "text/plain"
    return resp

            
    

if __name__ == '__main__':
    app.debug = True
    app.run(debug=True)
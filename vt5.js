/* vt5-javascript
author: Toni Pikkarainen
date: 1.11.2016
*/

/*
Sivulle tullessa näkyy vain kirjautuminen.
*/
window.onload = function() {
    $("#tunnus").val("");
    $("#salasana").val("");
    
    $("#lomake").hide();
    
    $("#uusi_elokuva").hide();
    $("#uusi_jasen").hide();
 
    $("#laheta_kirjaus").on("click", laheta_kirjaus);
    
    $("#logout").on("click",logout);
    $("#elo_valinta").on("click",elo_valinta);
    $("#vuokraus_valinta").on("click",vuokraus_valinta);
    $("#jasen_valinta").on("click",jasen_valinta);
    $(".navbar").hide();
}


/*
Funktiolla voidaan hakea sisältöä
tietokannassa sivulle.
*/
function hae_sisalto(funk,type,id) {
$.ajax({
        
        async: true,
        
        url: "/~totapikk/cgi-bin/vt5/flask.cgi/"+funk,
        
        type: "GET",
        
        dataType: type,
        
        beforeSend: function () {
               $(".modal").show();
            },
        complete: function () {
                $(".modal").hide();
            },
        success:function(data, textStatus, request){
         lisaa(id,data,textStatus,request)
        } , 
        error: ajax_virhe  
});
}


/*
Funktiolla esitetään virheilmoitus logiin jos
ajax-kutsu ei onnistu.
*/
function ajax_virhe(xhr, status, error) {
        console.log( "Error: " + error );
        console.log( "Status: " + status );
        console.log( xhr );
}

/*
Tällä lisätään tietokannassa haettua xml-muotoista dataa
sivulle.
*/
function lisaa(teksti, data, textStatus, request) {
   var select = document.importNode(request.responseXML.documentElement, 1);
   $(teksti).replaceWith(select);
   //$('#jasen').on("change",); 
   if(teksti=="#vuokraukset"){
    $(".vuokraus").on("click", muok_vuokraus) 
   }
  
}

/*
Uloskirjautuminen. Aiheuttaa palvelimella sessio-id:n tyhjentämisen.
*/
function logout() {
$.ajax({
        // tämä on oltava aina true. synkronista versiota ei pidä käyttää koska se voi jumittaa koko ohjelman
        async: true,
        // osoite jota kutsutaan eli aiemmin tehdyn flask-sovelluksen osoite
        url: "/~totapikk/cgi-bin/vt5/flask.cgi/logout",
        // POST tai GET. Nyt vain pyydetään tietoja eikä tehdä muutoksia joten GET
        type: "POST",
        // tietotyyppi jossa muodossa odotetaan vastausta vrt. flask-sovelluksessa määritetty text/plain
        dataType: "text",
        // parametrina viety data avain:arvo 
        //data: { 
        //    "postinro": $('#postinro').val()
        //},
        beforeSend: function () {
               $(".modal").show();
            },
        complete: function () {
                $(".modal").hide();
            },
        success: ulos_kirjaus,// funktio jota kutsutaan jos kaikki onnistuu
        error: ajax_virhe  // funktio jota kutsutaan jos tulee virhe
});
}

/*
Piilotetaan ja näytetään sivun elementtejä kun on
painettu elokuvat-linkkiä navigointipalkissa.
*/
function elo_valinta(){
    $("#virhe").text("");
    //$("#lomake").hide();
    //$("#elokuvat").show();
    $("#vuokraukset").hide();
    $("#jasen_info").hide();
    $("#elokuva_info").show();
    $("#vpvm_info").hide();
    $("#ppvm_info").hide();
    $("#kirjauslomake").hide();
    $("#laheta").hide();
    $("#muokkaa_vuok").hide();
    
    $("#uusi_elokuva").show();
    $("#uusi_jasen").hide();
    hae_sisalto("hae_lajityypit","xml","#lajityypit");

}

/*
Piilotetaan ja näytetään sivun elementtejä kun on
painettu jäsen-linkkiä navigointipalkissa.
*/
function jasen_valinta(){
    $("#virhe").text("");
    //$("#lomake").hide();
    //$("#elokuvat").show();
    $("#vuokraukset").hide();
    $("#jasen_info").show();
    $("#elokuva_info").hide();
    $("#vpvm_info").hide();
    $("#ppvm_info").hide();
    $("#kirjauslomake").hide();
    $("#laheta").hide();
    $("#muokkaa_vuok").hide();
    
    $("#uusi_elokuva").hide();
    $("#uusi_jasen").show();
   

}

/*
Piilotetaan ja näytetään sivun elementtejä kun on
painettu vuokraus-linkkiä navigointipalkissa.
*/
function vuokraus_valinta(){
   
    hae_sisalto("hae_vuokraukset","xml","#vuokraukset");
    $("#virhe").text("");
    $("#vuokraukset").show();
    $("#jasen_info").show();
    $("#elokuva_info").show();
    $("#vpvm_info").show();
    $("#ppvm_info").show();
    $("#kirjauslomake").hide();
    $("#uusi_jasen").hide();
    $("#laheta").show();
    $("#muokkaa_vuok").hide();
    
    $("#uusi_elokuva").hide();

}

/*
Piilotetaan ja näytetään sivun elementtejä kun on
painettu logout-linkkiä navigointipalkissa.
*/
function ulos_kirjaus(){
    $("#lomake").hide();
    $("#vuokraukset").hide();
    $("#kirjauslomake").show();
    $("#tunnus").val("");
    $("#salasana").val("");
    $(".navbar").hide();
    
}


/*
Funktio lähettää ajax-kutsun, jonka toteutuessa palvelinpuolen
ohjelma lisää vuokrauksen tietokantaan.
*/
function laheta(e) {
e.preventDefault();


$.ajax({
       
        async: true,
        
        url: "/~totapikk/cgi-bin/vt5/flask.cgi/lisaa_vuokraus",
        type: "POST",
        
        dataType: "text",
        
        beforeSend: function () {
               $(".modal").show();
            },
        complete: function () {
                $(".modal").hide();
            },
        data: $("#lomake").serialize(),
        success: hae_tiedot_vuok, 
        error: ajax_virhe  
});
}
/*
Tutkitaan, onko kirjautuminen onnistunut. Jos on, näytetään
sivun tietoja.
*/
function tutki_kirjautuminen(data, textStatus, request) {
    $("#virhe_kirjaus").text("");
    $("#virhe_kirjaus").text(data);

    if (!data){
        $("#kirjauslomake").hide();
        hae_sisalto("hae_jasenet","xml","#jasen");
        hae_sisalto("hae_elokuvat","xml","#elokuva");
        hae_sisalto("hae_vuokraukset","xml","#vuokraukset");
        $("#laheta").prop('disabled', false);
        $("#laheta").on("click", laheta);
        $("#poista_elokuva").on("click",{funk:"poista_elokuva"}, poista_tai_lisaa);
        $("#poista_jasen").on("click",{funk:"poista_jasen"}, poista_tai_lisaa);
        $("#lisaa_elokuva").on("click",{funk:"uusielokuva"}, poista_tai_lisaa);
        $("#lisaa_jasen").on("click",{funk:"uusijasen"}, poista_tai_lisaa);
        $("#muokkaa_vuok").hide();
        $("#vpvm").val("");
        $("#ppvm").val("");
        $("#kirjauslomake").hide();
        //$("#kirjausots").hide();
        $("#lomake").show();
        $("#vuokraukset").show();
        $(".navbar").show();
    }

}


/*
Tällä funktiolla voidaan poistaa tai lisätä esimerkiksi jäsen tai elokuva.
*/
function poista_tai_lisaa(e){
e.preventDefault();
var funk = e.data.funk;

$.ajax({
        
        async: true,
        
        url: "/~totapikk/cgi-bin/vt5/flask.cgi/"+funk,
        type: "POST",
        
        dataType: "text",
        
        beforeSend: function () {
               $(".modal").show();
            },
        complete: function () {
                $(".modal").hide();
            },
        data: $("#lomake").serialize(),
        success: hae_tiedot, 
        error: ajax_virhe  
});
}

/*
Asettaa palvelimelta tulleen mahdollisen virheilmoituksen
ja hakee sisältöä.
*/
function hae_tiedot(data, textStatus, request) {
    $("#virhe").text("");
    $("#virhe").text(data);
    
    $("input:text").each(function(){
        $(this).val("");
    });
    
    hae_sisalto("hae_elokuvat","xml","#elokuva");
    hae_sisalto("hae_jasenet","xml","#jasen");
 
}

/*
Asettaa palvelimelta tulleen mahdollisen virheilmoituksen
ja hakee sisältöä.
*/
function hae_tiedot_vuok(data, textStatus, request) {
    $("#virhe").text("");
    $("#virhe").text(data);
    
    $("input:text").each(function(){
        $(this).val("");
    });
    
    hae_sisalto("hae_elokuvat","xml","#elokuva");
    hae_sisalto("hae_jasenet","xml","#jasen");
    hae_sisalto("hae_vuokraukset","xml","#vuokraukset");
  
}

/*
Lähettää tiedon kirjautumisyrityksestä.
*/
function laheta_kirjaus(e) {
e.preventDefault();

$.ajax({
        
        async: true,
        
        url: "/~totapikk/cgi-bin/vt5/flask.cgi/kirjaudu",
        type: "get",
        
        dataType: "text",
        beforeSend: function () {
               $(".modal").show();
            },
        complete: function () {
                $(".modal").hide();
            },
        data: $("#kirjauslomake").serialize(),
        success: tutki_kirjautuminen, 
        error: ajax_virhe  
});
}

/*
Asettaa lomakkeelle sen vuokrauksen tiedot, jota on vuokrauslistasta
klikattu.
*/
function muok_vuokraus(){
    
    var eid=$(this).data("eid");
    var jid=$(this).data("jid");
    var vpvm=$(this).data("vpvm");
    var ppvm=$(this).data("ppvm");
 
    $("#muokkaa_vuok").show();
    $("#laheta").hide();
    
    $("#vpvm").val(vpvm);
    $("#ppvm").val(ppvm);
    muok_select(eid, "#elokuva option");
    muok_select(jid, "#jasen option");
    $("#muokkaa_vuok").off();
    $("#muokkaa_vuok").on("click",{eid:eid, jid:jid, vpvm:vpvm },laheta_muokkaus)
}

/*
Asettaa select-elementistä tietyn optionin valituksi
id:n perusteella. id kertoo mikä valitaan ja kenttä
kertoo, mistä select-elementistä on kyse.
*/
function muok_select(id,kentta ){
    $(kentta).each(function() {
    if( id == $(this).val()){
        $(this).prop("selected",true);
    }
    else{
        $(this).prop("selected",false);
    }
  });
}

/*
Lähettää tiedon siitä mitä vuokrausta muokataan ja
mitä siitä muokataan.
*/
function laheta_muokkaus(e) {
    e.preventDefault();
    
    var data=e.data;
   
    $.ajax({
        
        async: true,
        
        url: "/~totapikk/cgi-bin/vt5/flask.cgi/paivita_vuokraus",
        type: "GET",
        
        dataType: "text",
        
        beforeSend: function () {
               $(".modal").show();
            },
        complete: function () {
                $(".modal").hide();
            },
        data: { 
            "ueid": $("#elokuva").val(),
            "ujid": $("#jasen").val(),
            "uvpvm": $("#vpvm").val(),
            "uppvm":$("#ppvm").val(),
            "eid":data.eid,
            "jid":data.jid,
            "vpvm":data.vpvm
        }, 
        success: tutki_vuokraus_paivitys, 
        error: ajax_virhe  
});
}

/*
Tutkitaan onnistuiko vuokrauksen muokkaus.
*/
function tutki_vuokraus_paivitys(data, textStatus, request) {
    $("#virhe").text("");
    $("#virhe").text(data);
    if (!$.trim(data)){
        $("#muokkaa_vuok").hide();
        $("#laheta").show();
        hae_sisalto("hae_elokuvat","xml","#elokuva");
        hae_sisalto("hae_jasenet","xml","#jasen");
        hae_sisalto("hae_vuokraukset","xml","#vuokraukset");
        $("#vpvm").val("");
        $("#ppvm").val("");
    }
     
}




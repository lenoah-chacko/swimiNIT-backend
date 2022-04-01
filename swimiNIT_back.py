from flask import Flask,request
from flask import jsonify
from flask_cors import CORS
import datetime


import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate("./swiminit05-firebase-adminsdk-913f4-ea5d62a6c3.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
visits = db.collection(u'Visits')

app= Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

#########################################################################################################################
	
@app.route("/")
def index():
	response = jsonify(message="Simple server is running")
	return response
	
#########################################################################################################################		
	
@app.route("/get_details")
def get_details():
    caller=request.json['caller']

    try:
        visits = db.collection(u'Visits')
        memvisits=visits.where( u"membershipID", u"==", u"B190657CS").stream()
        visitarr=[]
        for memvisit in memvisits:
            visitarr.append(memvisit.to_dict())
        return jsonify({'visits':visitarr})
    except:
        return jsonify({'error':"exception"})

@app.route("/getLiveSwimmers")
def getLiveSwimmers():
    try:
        visits = db.collection( u'Visits')
        swimmer=db.collection( u'Swimmer')
        livevisits = visits.where( u"endTime", u"==", u"NULL").stream()
        visitarr=[]
        for livevisit in livevisits:
            temp=livevisit.to_dict()
            print(temp['membershipID'])
            liveswimmer=swimmer.where( u"membershipID", u"==", temp['membershipID']).get()
            liveswimmer=liveswimmer[0].to_dict()
            visitarr.append({ "swimmer":liveswimmer,"visit":temp})
        return jsonify({"visits:":visitarr})
    except:
        return jsonify({'error':"exception"})

@app.route("/register",methods=["POST"])
def register():
    paid=request.json['paid']
    details=request.json['details']
    memID=request.json['details'].membershipID
    try:
        swimmer=db.collection( u'Swimmer')
        swimmer.document(memID).set(details)
        return jsonify(details)
        if paid:
            Receipt = db.collection( u'ReceiptDetails')
            receiptdetails=request.json['receipt']
            receiptID=request.json['receipt'].receiptID
            Receipt.document(receiptID).set(receiptdetails)
    except:
        return jsonify({'error':"exception"})

@app.route("/getdetails",methods=["GET"])
def getdetails():
    memID=request.json["membershipID"]
    highAccess=request.json["admin"]
    try:
        swimmer=db.collection( u'Swimmer')
        details=swimmer.where( u"membershipID", u"==", memID).get()
        details=details[0].to_dict()
        if highAccess:
            return jsonify(details)
        else:
            return jsonify( {"name":details.name,"membershipID":memID,"emailID":details.emailID,"fees":details.fees,"dues":details.dues,"roles":details.role})
    except:
        return jsonify({'error':"exception"})

@app.route("/getreceiptdetails",methods=["GET"])
def getreceiptdetails():
    memID=request.json["membershipID"]
    try:
        receipts = db.collection( u'ReceiptDetails')
        today=datetime.datetime.now()
        print(today)
        validreceipts=receipts.where( u"membershipID", u"==", memID).get()
        for validreceipt in validreceipts:
            validreceipt=validreceipt.to_dict()
            validuntil=0
            receiptdate=validreceipt['validUntil']
            print(receiptdate)
            year,month,day=int(receiptdate[6:10]),int(receiptdate[3:5]),int(receiptdate[0:2])
            validuntil=datetime.datetime(year, month, day)
            print(validuntil)
            if today<validuntil:
                return jsonify({"receipt":validreceipt}) 
        return jsonify({'error':'User has not paid'}) 
    except:
        return jsonify({'error':"User has not paid"})


@app.route("/entry",methods=["POST"])
def entry():
    memID=request.json["membershipID"]
    details=request.json['details']
    try:
        swimmer=db.collection( u'Swimmer')
        details=swimmer.where( u"membershipID", u"==", memID).get()
        details=details[0].to_dict()
        try:
            visits = db.collection( u'Visits')
            visits.document(memID+details.dateOfVisit).set(details)
        except:
            return jsonify({'error':"Adding visit failed"})
    except:
        return jsonify({'error':"Swimmer doesn't exist"})

@app.route("/exit",methods=["POST"])
def exit():
    memID=request.json["membershipID"]
    endTime=request.json["endTime"]
    try:
        swimmer=db.collection( u'Swimmer')
        details=swimmer.where( u"membershipID", u"==", memID).get()
        details=details[0].to_dict()
        try:
            visits = db.collection( u'Visits')
            memvisits=visits.where( u"membershipID", u"==", memID).where( u"endTime", u"==", u"NULL").get()
            if len(memvisits)>0:
                notexited=memvisits[0].to_dict()
                print(memID+notexited['dateOfVisit'])
                visits.document(memID+notexited['dateOfVisit']).update({u'endTime':endTime})
                return jsonify({"membershipID":memID,"dateOfVisit":notexited['dateofVisit'],"endTime":endTime})
            else:
                return jsonify({'error':"User has already exited"})
        except:
            return jsonify({'error':"exiting visit failed"})
    except:
        return jsonify({'error':"Swimmer doesn't exist"})

@app.route("/getUserVisits",methods=["GET"])
def getUserVisits():
    memID=request.json["membershipID"]
    try:
        swimmer=db.collection( u'Swimmer')
        details=swimmer.where( u"membershipID", u"==", memID).get()
        details=details[0].to_dict()
        try:
            visits = db.collection( u'Visits')
            uservisits=visits.where(u"membershipID",u"==",memID).get()
            uservisitsarr=[]
            for uservisit in uservisits:
                uservisit=uservisit.to_dict()
                uservisitsarr.append(uservisit)
            return jsonify({"membershipID":memID,"visits":uservisitsarr})
        except:
            return jsonify({'error':"Adding visit failed"})
    except:
        return jsonify({'error':"Swimmer doesn't exist"})

@app.route("/getDateVisits",methods=["GET"])
def getDateVisits():
    startDate=request.json["startDate"]
    endDate=request.json["endDate"]
    try:
        year,month,day=int(startDate[6:10]),int(startDate[3:5]),int(startDate[0:2])
        startDate=datetime.datetime(year, month, day)
        print(startDate)
        year,month,day=int(endDate[6:10]),int(endDate[3:5]),int(endDate[0:2])
        endDate=datetime.datetime(year, month, day)
        print(endDate)

        visits = db.collection( u'Visits')
        uservisits=visits.stream()
        uservisitsarr=[]
        for uservisit in uservisits:
            uservisit=uservisit.to_dict()
            dateOfVisit=uservisit['dateOfVisit']
            year,month,day=int(dateOfVisit[6:10]),int(dateOfVisit[3:5]),int(dateOfVisit[0:2])
            visitedDate=datetime.datetime(year, month, day)
            if visitedDate>startDate and visitedDate<endDate:
                uservisitsarr.append(uservisit)
        return jsonify({"membershipID":memID,"visits":uservisitsarr})
    except:
        return jsonify({'error':"Adding visit failed"})

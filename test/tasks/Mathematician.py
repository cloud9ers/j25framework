from celery.decorators import task
from test.dummy.document import TestDocument
from j25.model.Document import Document

@task
def add(x, y):
    return x+y

@task
def playWithModel():
    doc = TestDocument(55, "Ismail", 75)
    doc.save()
    return TestDocument.count()

@task
def getModelObj(id):
    doc = TestDocument.findOne(Document({'id': id}))
    return doc.toDict()

@task
def kaboom():
    raise Exception("Kaboom")
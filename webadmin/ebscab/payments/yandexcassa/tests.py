#-*- coding: utf-8 -*-

from django.test import TestCase
from django.core.urlresolvers import reverse

from django.test.client import Client
from billservice.models import Account, Transaction, TransactionType
import datetime
from BeautifulSoup import BeautifulSoup

class SimpleTest(TestCase):
    
    def setUp(self):

        acc = Account()
        acc.username='010001'
        acc.password='010001'
        acc.fullname='foouser'
        acc.created = datetime.datetime.now()
        acc.contract = '010001'
        acc.save()
        
        self.acc = acc
        
    def test_check(self):

        params = {
            'scid': 12345,
            'requestDatetime': '2011-05-04T20:38:00.000+04:00',
            'action': 'checkOrder',
            'shopId': 54321,
            'shopArticleId': '456',
            'invoiceId': '1234567',
            'orderCreatedDatetime': '2011-05-04T20:38:00.000+04:00',
            'orderSumAmount': '87.10',
            'orderSumCurrencyPaycash': '643',
            'orderSumBankPaycash': '1001',
            'shopSumAmount': '86.23',
            'shopSumCurrencyPaycash': '643',
            'shopSumBankPaycash': '1001',
            'paymentPayerCode': '42007148320',
            'paymentType': 'GP',
        }
    
        response = c.post(reverse('getpaid-easypay-pay'), """<Request>
<DateTime>yyyy-MM-ddTHH:mm:ss</DateTime>
<Sign></Sign>
<Check>
<ServiceId>int</ServiceId>
<Account>010001</Account>
</Check>
</Request>""", content_type='text/xml')
        print response.content
        

    def test_pay(self):
        c = Client()
        acc = Account()
        acc.username='010001'
        acc.password='010001'
        acc.fullname='foouser'
        acc.created = datetime.datetime.now()
        acc.contract = '010001'
        acc.save()
        response = c.post(reverse('getpaid-easypay-pay'), """<Request>
<DateTime>yyyy-MM-ddTHH:mm:ss</DateTime>
<Sign></Sign>
<Payment>
<ServiceId>1</ServiceId>
<OrderId>1</OrderId>
<Account>010001</Account>
<Amount>10.11</Amount>
</Payment>
</Request>""", content_type='text/xml')
        print response.content
        
    def test_confirm(self):
        c = Client()
        acc = Account()
        acc.username='010001'
        acc.password='010001'
        acc.fullname='foouser'
        acc.created = datetime.datetime.now()
        acc.contract = '010001'
        acc.save()
        TransactionType.objects.create(name='EasyPay', internal_name = 'payments.easypay')
        
        response = c.post(reverse('getpaid-easypay-pay'), """<Request>
<DateTime>yyyy-MM-ddTHH:mm:ss</DateTime>
<Sign></Sign>
<Payment>
<ServiceId>1</ServiceId>
<OrderId>1</OrderId>
<Account>010001</Account>
<Amount>10.11</Amount>
</Payment>
</Request>""", content_type='text/xml')
        print response.content
        bs = BeautifulSoup(response.content)
        response = c.post(reverse('getpaid-easypay-pay'), """<Request>
<DateTime>yyyy-MM-ddTHH:mm:ss</DateTime>
<Sign></Sign>
<Confirm>
<ServiceId>1</ServiceId>
<PaymentId>%s</PaymentId>
</Confirm>
</Request>""" % bs.response.paymentid, content_type='text/xml')
        
        print 'TRANSACTION=', Transaction.objects.get(type__internal_name='payments.easypay', bill='1')
        
        print response.content
        
    def test_cancel(self):
        c = Client()
        acc = Account()
        acc.username='010001'
        acc.password='010001'
        acc.fullname='foouser'
        acc.created = datetime.datetime.now()
        acc.contract = '010001'
        acc.save()
        TransactionType.objects.create(name='EasyPay', internal_name = 'payments.easypay')
        
        response = c.post(reverse('getpaid-easypay-pay'), """<Request>
<DateTime>yyyy-MM-ddTHH:mm:ss</DateTime>
<Sign></Sign>
<Payment>
<ServiceId>1</ServiceId>
<OrderId>1</OrderId>
<Account>010001</Account>
<Amount>10.11</Amount>
</Payment>
</Request>""", content_type='text/xml')
        print response.content
        bs = BeautifulSoup(response.content)
        response = c.post(reverse('getpaid-easypay-pay'), """<Request>
<DateTime>yyyy-MM-ddTHH:mm:ss</DateTime>
<Sign></Sign>
<Confirm>
<ServiceId>1</ServiceId>
<PaymentId>%s</PaymentId>
</Confirm>
</Request>"""  % bs.response.paymentid, content_type='text/xml')
        
        response = c.post(reverse('getpaid-easypay-pay'), """<Request>
<DateTime>yyyy-MM-ddTHH:mm:ss</DateTime>
<Sign></Sign>
<Cancel>
<ServiceId>1</ServiceId>
<PaymentId>%s</PaymentId>
</Cancel>
</Request>""" % bs.response.paymentid, content_type='text/xml')
        self.assertEqual(Transaction.objects.filter(type__internal_name='payments.easypay', bill='1').count(), 0)
        
        print response.content
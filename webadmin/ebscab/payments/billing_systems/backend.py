# -*- coding: utf-8 -*-

import hashlib

from django.utils.translation import ugettext_lazy as _

from billservice.models import Account
from getpaid.backends import PaymentProcessorBase
from getpaid.models import Payment


BODY = u'''\
<?xml version="1.0" encoding="utf-8"?>
<request>
    <params>%(BODY)s</params>
    <sign>%(SIGN)s</sign>
</request>'''

BODY_ERR = u'''\
<?xml version="1.0" encoding="utf-8"?>
<request>
    <params>%(BODY)s</params>
    <sign>%(SIGN)s</sign>
</request>'''

CHECK_BODY_SUCCESS = u'''\
<err_code>%(ERR_CODE)s</err_code>
<err_text>%(ERR_TEXT)s</err_text>
<account>%(ACCOUNT)s</account>
<client_name>%(CLIENT_NAME)s</client_name>
<balance>%(BALLANCE)s</balance>'''

CHECK_BODY_ERROR = u'''\
<err_code>%(ERR_CODE)s</err_code>
<err_text>%(ERR_TEXT)s</err_text>'''

PAYMENT_BODY = u'''\
<err_code>%(ERR_CODE)s</err_code>
<err_text>%(ERR_TEXT)s</err_text>
<account>%(ACCOUNT)s</account>'''

PAYMENT_FREAK_BODY = u'''\
<err_code>%(ERR_CODE)s</err_code>
<err_text>%(ERR_TEXT)s</err_text>
<account>%(ACCOUNT)s</account>'''

# FIXME: translation
ERRCODES = {
    '0': u'Успешное выполнение операции',
    '1': u'Платеж уже был проведен',
    '10': u'Запрос выполнен с неразрешенного адреса',
    '11': u'Указаны не все необходимые параметры ',
    '12': u'Неверный формат параметров',
    '13': u'Неверная цифровая подпись',
    '20': u'Указанный номер счета отсутствует',
    '21': u'Запрещены платежи на указанный номер счета',
    '22': u'Запрещены платежи для указанной услуги',
    '23': u'Запрещены платежи для указанного агента',
    '29': u'Неверные параметры платежа.',
    '30': u'Был другой платеж с указанным номером',
    '90': u'Временная техническая ошибка',
    '99': u'Прочие ошибки Оператора. '
}


class TransactionStatus:
    OK = 0
    ERROR = 1


class PaymentProcessor(PaymentProcessorBase):
    BACKEND = 'payments.billing_systems'
    BACKEND_NAME = _('billing systems backend')
    BACKEND_ACCEPTED_CURRENCY = ('RUB',)

    def get_gateway_url(self, request, payment):
        return self.GATEWAY_URL, 'GET', {}

    @staticmethod
    def error(body, code, text=''):
        body_error = CHECK_BODY_ERROR.encode('utf-8') % {
            'ERR_CODE': code,
            'ERR_TEXT': (text.encode('utf-8') or
                         ERRCODES.get(str(code)).encode('utf-8'))
        }

        return BODY_ERR.encode('utf-8') % {
            'BODY': body_error,
            'SIGN': PaymentProcessor.compute_sig(body, body_error)
        }

    @staticmethod
    def compute_sig(body, text):
        req_sign = (body.request.sign.text if body.request.sign
                    else '').encode('utf-8')

        s = text + req_sign + \
            PaymentProcessor.get_backend_setting(
                'PASSWORD', '').encode('utf-8')
        sign = hashlib.md5(s).hexdigest()

        return sign

    @staticmethod
    def check_sig(body):
        req_sign = (body.request.sign.text if body.request.sign
                    else '').encode('utf-8')
        if not req_sign:
            return False

        text = (u''.join(unicode(item) for item in
                         body.request.params.contents)).encode('utf-8')

        s = text + (PaymentProcessor
                    .get_backend_setting('PASSWORD', '')
                    .encode('utf-8'))
        sign = hashlib.md5(s).hexdigest()

        return req_sign.lower() == sign.lower()

    @staticmethod
    def check(request, body):
        acc = body.request.params.account.text
        try:
            account = Account.objects.get(contract=acc)
        except Account.DoesNotExist, ex:
            return PaymentProcessor.error(body, 20)

        pay_amount = (body.request.params.pay_amount.text
                      if body.request.params.pay_amount else 0)
        if not pay_amount:
            return PaymentProcessor.error(body, 29)

        body_error = CHECK_BODY_SUCCESS % {
            'ERR_CODE': 0,
            'ERR_TEXT': ERRCODES.get('0'),
            'ACCOUNT': account.contract,
            'CLIENT_NAME': unicode(account.fullname),
            'BALLANCE': '%.2f' % float(account.ballance),
        }

        body_error = unicode(body_error).encode('utf-8')

        ret = BODY.encode('utf-8') % {
            'BODY': body_error,
            'SIGN': str(PaymentProcessor
                        .compute_sig(body, body_error)
                        .encode('utf-8'))
        }
        return ret

    @staticmethod
    def pay(request, body):
        acc = body.request.params.account.text
        amount = float(body.request.params.pay_amount.text) / 100
        paymentid = body.request.params.pay_id.text

        try:
            account = Account.objects.get(contract=acc)
        except Account.DoesNotExist, ex:
            return PaymentProcessor.error(body, 20)
        payment = None
        try:
            payment = Payment.objects.get(external_id=paymentid)
            if payment.status == 'paid':
                print 'was already paid'
                return PaymentProcessor.error(body, 30)
            if payment.account != account.contract or payment.amount != amount:
                print 'incorrect amount'
                return PaymentProcessor.error(body, 30)
        except Exception, e:
            print e

        if not payment:
            payment = Payment.create(account,
                                     None,
                                     PaymentProcessor.BACKEND,
                                     amount=amount,
                                     external_id=paymentid)

        reply_body = PAYMENT_BODY.encode('utf-8') % {
            'ERR_CODE': 0,
            'ERR_TEXT': ERRCODES.get('0'),
            'ACCOUNT': account.contract,
            'BALLANCE': '%.2f' % float(account.ballance or 0)
        }
        reply_body = reply_body.encode('utf-8')
        ret = BODY.encode('utf-8') % {
            'BODY': reply_body,
            'SIGN': PaymentProcessor.compute_sig(body, reply_body)
        }

        if payment.status != 'paid':
            payment.change_status('paid')
        return ret

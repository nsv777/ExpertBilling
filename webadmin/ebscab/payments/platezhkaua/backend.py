# -*- coding: utf-8 -*-

import datetime

from django.utils.translation import ugettext_lazy as _

from billservice.models import Account
from getpaid.backends import PaymentProcessorBase
from getpaid.models import Payment


ERROR_TEMPLATE = u'''\
<?xml version="1.0" encoding="UTF-8"?>
<commandResponse>
    <extTransactionID>%(TRANSACTION_ID)s</extTransactionID>
    <account>%(ACCOUNT)s</account>
    <result>%(RESULT)s</result>
    <comment>%(COMMENT)s</comment>
</commandResponse>'''

SUCCESS_CHECK_TEMPLATE = u'''\
<?xml version="1.0" encoding="UTF-8"?>
<commandResponse>
    <extTransactionID>%(TRANSACTION_ID)s</extTransactionID>
    <account>%(ACCOUNT)s</account>
    <result>%(RESULT)s</result>
    <comment>%(COMMENT)s</comment>
</commandResponse>'''


class TransactionStatus:
    OK = 0
    ERROR = 1


class PaymentProcessor(PaymentProcessorBase):
    BACKEND = 'payments.platezhkaua'
    BACKEND_NAME = _('Platezhka UA backend')
    BACKEND_ACCEPTED_CURRENCY = ('UAH',)

    GATEWAY_URL = ''

    _ALLOWED_IP = ('62.149.15.210',)

    @staticmethod
    def check_allowed_ip(ip, request, body):
        allowed_ip = PaymentProcessor.get_backend_setting(
            'allowed_ip', PaymentProcessor._ALLOWED_IP)

        if len(allowed_ip) != 0 and ip not in allowed_ip:
            return PaymentProcessor.error(body, _(u'Unknown IP'))
        return 'OK'

    @staticmethod
    def check_credentials(request, body):
        login = PaymentProcessor.get_backend_setting('LOGIN')
        password = PaymentProcessor.get_backend_setting('PASSWORD')

        if login != body.commandcall.login.text or \
                password != body.commandcall.password.text:
            return PaymentProcessor.error(body, 300, _(u'Incorrect credentials'))
        return 'OK'

    def get_gateway_url(self, request, payment):
        return self.GATEWAY_URL, 'GET', {}

    @staticmethod
    def error(body, text, comment=''):
        return ERROR_TEMPLATE % {
            'TRANSACTION_ID': body.commandcall.transactionid.text,
            'RESULT': text,
            'ACCOUNT': body.commandcall.account.text,
            'COMMENT': comment
        }

    @staticmethod
    def check(request, body):
        acc = body.commandcall.account.text
        try:
            _ = Account.objects.get(contract=acc)
        except Account.DoesNotExist, ex:
            return PaymentProcessor.error(body, 5, _(u'Аккаунт не найден'))

        ret = ERROR_TEMPLATE % {
            'TRANSACTION_ID': body.commandcall.transactionid.text,
            'RESULT': 0,
            'ACCOUNT': body.commandcall.account.text,
            'COMMENT': 'OK'
        }

        return ret

    @staticmethod
    def pay(request, body):
        acc = body.commandcall.account.text
        amount = float(body.commandcall.amount.text) / 100.00
        orderid = body.commandcall.payid.text
        timestamp = body.commandcall.paytimestamp.text

        try:
            account = Account.objects.get(contract=acc)
        except Account.DoesNotExist, ex:
            return PaymentProcessor.error(body, 5, _(u'Аккаунт не найден'))

        if amount > 0:
            payment = Payment.create(
                account,
                None,
                PaymentProcessor.BACKEND,
                amount=amount,
                external_id=orderid)
            payment.paid_on = datetime.datetime.strptime(
                timestamp, '%Y%m%d%H%M%S')
            payment.amount_paid = payment.amount
            payment.save()
            payment.change_status('paid')
            ret = SUCCESS_CHECK_TEMPLATE % {
                'TRANSACTION_ID': body.commandcall.transactionid.text,
                'RESULT': 0,
                'ACCOUNT': body.commandcall.account.text,
                'COMMENT': 'OK',
            }

            return ret
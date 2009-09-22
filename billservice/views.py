 #-*- coding=UTF-8 -*-
 
import datetime
import Pyro.core
import Pyro.protocol
import Pyro.constants
import Pyro.errors

from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django import template

from lib.http import JsonResponse

from django.conf import settings
from billservice.models import Account, AccountTarif, NetFlowStream, Transaction, Card, TransactionType, TrafficLimit, Tariff, TPChangeRule, AddonService, AddonServiceTarif, AccountAddonService 
from billservice.forms import LoginForm, PasswordForm, CardForm, ChangeTariffForm, PromiseForm
from billservice import authenticate, log_in, log_out
from radius.models import ActiveSession  
from billservice.utility import is_login_user, settlement_period_info
from nas.models import TrafficClass

from lib.decorators import render_to, ajax_request



@render_to('registration/login.html')
def login(request):
    error_message = True
    if request.method == 'POST':
        pin=request.POST.get('pin','')
        user = request.POST.get('user','')
        if pin!='':
            if user!='':
                message=None
                try:
                    connection_server = Pyro.core.getProxyForURI("PYROLOC://%s:7766/rpc" % unicode(settings.RPC_ADDRESS))
                    import hashlib
                    md1 = hashlib.md5(settings.RPC_PASSWORD)
                    md1.hexdigest()
                   
                    password = str(md1.hexdigest())
                    connection_server._setNewConnectionValidator(antiMungeValidator())
                    connection_server._setIdentification("%s:%s:2" % (str(settings.RPC_USER), str(password)))
                    #connection_server.test()
                except Exception, e:
                    if isinstance(e, Pyro.errors.ConnectionDeniedError):
                        error_message = u"Отказано в авторизации."
                    else:
                        error_message  = u"Невозможно подключиться к серверу."
                message_type = connection_server.activate_card(user, pin)
                ok_message = False
                if message_type == 1:
                    message = u'Карточка успешно активирована. <br>  Выш логин %s <br> ваш пароль %s' % (user, pin)
                    ok_message = True
                if message_type == 2:
                    message = u'Не верно введен логин или пароль'
                if message_type == 3:
                    message = u'Карточка уже была активирована'
            form = LoginForm()
            return {
                    'form':form,
                    'message':message,
                    'ok_message':ok_message,
                    }
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                print form.cleaned_data['username']
                user = Account.objects.get(username=form.cleaned_data['username'])
                print "user=", user, user.id, user.allow_webcab
                if not user.allow_webcab:
                    form = LoginForm()
                    error_message = u'У вас нет прав на вход в веб-кабинет'
                    return {
                            'error_message':error_message,
                            'form':form,
                            } 
                print user.password, form.cleaned_data['password']
                if user.password == form.cleaned_data['password']:
                    user = authenticate(username=user.username, password=form.cleaned_data['password'])
                    log_in(request, user)
                    request.session['user'] = user
                    if not cache.get(user.id):
                        cache.set(user.id, {'count':0,'last_date':datetime.datetime.now(),'blocked':False,}, 86400*365)
                    else:
                        cache_user = cache.get(user.id)
                        if cache_user['blocked']:
                            cache.set(user.id, {'count':cache_user['count'],'last_date':cache_user['last_date'],'blocked':cache_user['blocked'],}, 86400*365)
                        else:
                            cache.set(user.id, {'count':cache_user['count'],'last_date':datetime.datetime.now(),'blocked':cache_user['blocked'],}, 86400*365)    
                    cursor = connection.cursor()
                    cursor.execute("""SELECT allow_express_pay FROM billservice_tariff WHERE id=get_tarif(%s)""" % (user.id))
                    allow_express_pay = cursor.fetchone()[0]
                    if allow_express_pay:
                        request.session['express_pay']=True
                    request.session.modified = True
                    return HttpResponseRedirect('/')
                else:
                    form = LoginForm(initial={'username': form.cleaned_data['username']})
                    error_message = u'Проверьте введенные данные'
                    return {
                            'error_message':error_message,
                            'form':form,
                            }
            except :
                form = LoginForm(initial={'username': form.cleaned_data['username']})
                error_message = u'Проверьте введенные данные'
                return {
                        'error_message':error_message,
                        'form':form,
                        }
        else:
            form = LoginForm(initial={'username': request.POST.get('username', None)})
            error_message = u'Проверьте введенные данные'
            return {
                    'error_message':error_message,
                    'form':form,
                    }
    else:
         form = LoginForm()
         return {
                 'form':form,
                }  
               
def login_out(request):
    if request.session.has_key('user'):
        del request.session['user']
    log_out(request)
    return is_login_user(request)


@render_to('accounts/index.html')
def index(request):
    if not request.session.has_key('user'):
        return is_login_user(request)
    user = request.session['user']
    if not cache.get(user.id):
        del request.session['user']
        return is_login_user(request)
    cursor = connection.cursor()
    cursor.execute("""SELECT id, name FROM billservice_tariff WHERE id=get_tarif(%s)""" % (user.id)) 
    tariff_id, tariff_name = cursor.fetchone()
    cache_user = cache.get(user.id)
    if int(cache_user['count']) > settings.ACTIVATION_COUNT and bool(cache_user['blocked']):
        time = datetime.datetime.now() - cache_user['last_date']
        if time.seconds > settings.BLOCKED_TIME:
            cache.delete(user.id)
            cache.set(user.id, {'count':0,'last_date':cache_user['last_date'],'blocked':False,}, 86400*365)
    date = datetime.date(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
    tariffs = AccountTarif.objects.filter(account=user, datetime__lt=date).order_by('-datetime')
    if len(tariffs) == 0 or len(tariffs) == 1:
        tariff_flag = False
    else:
        tariff_flag = True 
    try:
        ballance = user.ballance - user.credit
        ballance = u'%.2f' % user.ballance
    except:
         ballance = 0
    #find prepare trafick
    
    #cursor = connection.cursor()
    cursor.execute("""SELECT name FROM billservice_tariff WHERE id=get_tarif(%s)""" % (user.id)) 
    try:
        tariff = cursor.fetchone()[0]
        traffic = TrafficLimit.objects.filter(tarif=tariff_id) 
    except:
        traffic = None
        
    from billservice.models import AccountPrepaysTrafic, PrepaidTraffic
    

    cursor.execute("""select id FROM billservice_accounttarif WHERE account_id=%s and datetime<now()  ORDER BY id DESC LIMIT 1""" % (user.id)) 
    try:
        account_tariff_id = cursor.fetchone()[0]
        account_tariff = AccountTarif.objects.get(id=account_tariff_id)
        account_prepays_trafic = AccountPrepaysTrafic.objects.filter(account_tarif__id=account_tariff_id)
        prepaidtraffic = PrepaidTraffic.objects.filter(id__in=[ i.prepaid_traffic.id for i in account_prepays_trafic])
    except:
        prepaidtraffic = None 
    return {
            'account_tariff':account_tariff,
            'ballance':ballance,
            'tariff':tariff_name,
            'tariffs':tariffs,
            'status': bool(cache_user['blocked']),
            'tariff_flag':tariff_flag,
            'trafficlimit':traffic,
            'prepaidtraffic':prepaidtraffic,
            'form':  CardForm(),
            }
    
@render_to('accounts/netflowstream_info.html')
def netflowstream_info(request):
    if not request.session.has_key('user'):
        return is_login_user(request)
    from lib.paginator import SimplePaginator
    paginator = SimplePaginator(request, NetFlowStream.objects.filter(account=request.session['user']).order_by('-date_start'), 500, 'page')
    return {
            'net_flow_streams':paginator.get_page_items(),
            'paginator': paginator,
            }
    

@render_to('accounts/get_promise.html')
def get_promise(request):
    if not request.session.has_key('user'):
        return is_login_user(request)
    if settings.ALLOW_PROMISE==False:
        return HttpResponseRedirect('/')
    user = request.session['user']
    LEFT_PROMISE_DATE = datetime.datetime.now()+datetime.timedelta(days = settings.LEFT_PROMISE_DAYS)
    
    cursor = connection.cursor()
    cursor.execute("""SELECT True FROM billservice_transaction WHERE account_id=%s and promise=True and promise_expired=False""" % (user.id))
    #print "cursor.fetchone()", cursor.fetchone()
    if cursor.fetchone():
        last_promises = Transaction.objects.filter(account=user, promise=True).order_by('-created')[0:10]
        error_message = u"У вас есть незакрытые обещанные платежи"
        return {'error_message': error_message, 'LEFT_PROMISE_DATE': LEFT_PROMISE_DATE, 'disable_promise': True, 'last_promises': last_promises, }        
    #print 1
    if request.method == 'POST':
        rf = PromiseForm(request.POST)
        if not rf.is_valid():
            last_promises = Transaction.objects.filter(account=user, promise=True).order_by('-created')[0:10]
            error_message = u"Проверьте введённые в поля данные"
            return {'MAX_PROMISE_SUM': settings.MAX_PROMISE_SUM, 'error_message': error_message, 'LEFT_PROMISE_DATE': LEFT_PROMISE_DATE, 'disable_promise': False,  'last_promises': last_promises, }
        #print 2
        sum=rf.cleaned_data.get("sum", 0)
        if sum>settings.MAX_PROMISE_SUM:
            last_promises = Transaction.objects.filter(account=user, promise=True).order_by('-created')[0:10]
            error_message = u"Вы превысили максимальный размер обещанного платежа"
            return {'MAX_PROMISE_SUM': settings.MAX_PROMISE_SUM,'error_message': error_message, 'LEFT_PROMISE_DATE': LEFT_PROMISE_DATE, 'disable_promise': False,  'last_promises': last_promises, }
        #print 3
        if sum<=0:
            last_promises = Transaction.objects.filter(account=user, promise=True).order_by('-created')[0:10]
            error_message = u"Сумма обещанного платежа должна быть положительной"
            return {'MAX_PROMISE_SUM': settings.MAX_PROMISE_SUM,'error_message': error_message, 'LEFT_PROMISE_DATE': LEFT_PROMISE_DATE, 'disable_promise': False,  'last_promises': last_promises, }
        cursor.execute(u"""INSERT INTO billservice_transaction(account_id, bill, type_id, approved, tarif_id, summ, created, promise, end_promise, promise_expired) 
                          VALUES(%s, 'Обещанный платёж', 'MANUAL_TRANSACTION', True, get_tarif(%s), %s, now(), True, '%s', False)""" % (user.id, user.id, sum*(-1), LEFT_PROMISE_DATE))
        cursor.connection.commit()
        last_promises = Transaction.objects.filter(account=user, promise=True).order_by('-created')[0:10]
        
        return {'error_message': u'Обещанный платёж выполнен успешно. Обращаем ваше внимание на то, что повторно воспользоваться услугой обещанного платежа вы сможете после погашения суммы платежа или истечения даты созданного платежа.', 'disable_promise': True, 'last_promises': last_promises,}
    else:
        last_promises = Transaction.objects.filter(account=user, promise=True).order_by('-created')[0:10]
        return {'MAX_PROMISE_SUM': settings.MAX_PROMISE_SUM, 'last_promises': last_promises, 'disable_promise': False, 'LEFT_PROMISE_DATE': LEFT_PROMISE_DATE}     
            
        
    #from lib.paginator import SimplePaginator
    #paginator = SimplePaginator(request, NetFlowStream.objects.filter(account=request.session['user']).order_by('-date_start'), 500, 'page')
    

    
@render_to('accounts/transaction.html')
def transaction(request):
    if not request.session.has_key('user'):
        return is_login_user(request)
    from lib.paginator import SimplePaginator
    paginator = SimplePaginator(request, Transaction.objects.filter(account=request.session['user']).order_by('-created'), 100, 'page')
    return {
            'transactions':paginator.get_page_items(),
            'paginator': paginator,
            }
    
@render_to('accounts/vpn_session.html')
def vpn_session(request):
    if not request.session.has_key('user'):
        return is_login_user(request)
    from lib.paginator import SimplePaginator
    user = request.session['user']
    paginator = SimplePaginator(request, ActiveSession.objects.filter(account=user).order_by('-date_start'), 50, 'page')
    return {
            'sessions':paginator.get_page_items(),
            'paginator': paginator,
            'user': user,
            }
    

@render_to('accounts/services_info.html')    
def services_info(request):
    if not request.session.has_key('user'):
        return is_login_user(request)
    from lib.paginator import SimplePaginator
    user = request.session['user']  
    paginator = SimplePaginator(request, AccountAddonService.objects.filter(account=user).order_by('-activated'), 50, 'page')
    return {
            'services':paginator.get_page_items(),
            'paginator': paginator,
            'user': user,
            }
    
    
@render_to('accounts/change_password.html')
def card_form(request):
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    return {
            'form':PasswordForm()
            }

@ajax_request
def change_password(request):
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            try:
                user = request.session['user']
                print 1
                user = Account.objects.get(username=user.username)
                print 2
                if user.password == form.cleaned_data['old_password'] and form.cleaned_data['new_password']==form.cleaned_data['repeat_password']:
                    print 3
                    user.password = form.cleaned_data['new_password']
                    print 4
                    user.save()
                    print 5
                    return {
                            'error_message': u'Пароль успешно изменен',
                            'ok':'ok',
                            }
                else:
                    return {
                            'error_message': u'Проверьте пароль',
                            }
            except Exception, e:
                print e
                return {
                        'error_message': u'Возникла ошибка. Обратитесь к администратору.',
                        }
        else:
            return {
                    'error_message': u'Проверьте введенные данные',
                    }
    else:
        return {
                'error_message': u'Не предвиденная ошибка',
                }



@ajax_request
@render_to('accounts/change_tariff.html')
def change_tariff_form(request):
    from datetime import datetime, date 
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    user = request.session['user']
    cursor = connection.cursor()
    cursor.execute("""select id FROM billservice_accounttarif WHERE account_id=%s and datetime<now()  ORDER BY id DESC LIMIT 1""" % (user.id)) 
    account_tariff_id = cursor.fetchone()[0]
    account_tariff = AccountTarif.objects.get(id=account_tariff_id)
    #time = (datetime.now() - account_tariff.datetime).seconds
    tariffs = TPChangeRule.objects.filter(ballance_min__lte=user.ballance)
    #form = ChangeTariffForm(user, account_tariff)
    form = ChangeTariffForm(user, account_tariff)
    return {
            'form': form,
            'tariff_objects':tariffs,
            'user':request.session['user'],
            'tariff':account_tariff,
            #'time':time,
            }


@ajax_request
def change_tariff(request):
    """
        settlement_period_info
        1 - дата начала действия тарифа
        
    """
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        rule_id = request.POST.get('id_tariff_id', None)
        if rule_id != None:
            user = request.session['user']
            cursor = connection.cursor()
            cursor.execute("""select id FROM billservice_accounttarif WHERE account_id=%s and datetime<now()  ORDER BY id DESC LIMIT 1""" % (user.id))
            account_tariff_id = cursor.fetchone()[0]
            
            account_tariff = AccountTarif.objects.get(id=account_tariff_id)
            from datetime import datetime
            rules_id =[x.id for x in TPChangeRule.objects.filter(ballance_min__lte=user.ballance)]
            rule = TPChangeRule.objects.get(id=rule_id)
            #cursor.execute("SELECT name FROM billservice_accountaddonservice WHERE account_id=%s and")
            #settlement_period_info(time_start, repeat_after='', repeat_after_seconds=0,  now=None, prev = False)
            if rule.settlement_period_id:
                td = settlement_period_info(account_tariff.datetime, rule.settlement_period.length_in, rule.settlement_period.length)
                delta = (datetime.now() - account_tariff.datetime).seconds+(datetime.now() - account_tariff.datetime).days*86400 - td[2]
                if delta < 0:
                    return {
                            'error_message':u'Вы не можете перейти на выбранный тариф. Для перехода вам необходимо отработать на старом тарифе ещё не менее %s дней' % (delta/86400*(-1), ),
                            }
            if not rule.id in rules_id:
                return {
                        'error_message':u'Вы не можете перейти на выбранный тариф',
                        }
            tariff = AccountTarif.objects.create(
                                                    account = request.session['user'],
                                                    tarif = rule.to_tariff,
                                                    datetime = datetime.now(), 
                                                 )
            cursor.execute("UPDATE billservice_accountaddonservice SET deactivated=now() WHERE account_id = %s and deactivated is Null;" % user.id)
            return {
                    'ok_message':u'Вы успешно сменили тариф',
                    }
        else:
            return {
                    'error_message':u'Проверьте Ваш тариф',
                    }
    else:
        return {
                'error_message':u'Проверьте Ваш тариф',
                }


@ajax_request
def card_acvation(request):
    if not request.session.has_key('user'):
        return {
                'redirect':'/login/',
               }
                #HttpResponseRedirect('/')
    if not request.session.has_key('express_pay'):
        return {
                'error_message': u'Вам не доступна услуга активации карт экспресс оплаты!',
               }
    user = request.session['user']
    if not user.allow_expresscards:
        return {
                'error_message': u'Вам не доступна услуга активации карт экспресс оплаты!',
                }
    if not cache.get(user.id):
        return {
                'redirect':'/login/',
               }
        #HttpResponseRedirect('/')
    cache_user = cache.get(user.id)
    if int(cache_user['count']) > settings.ACTIVATION_COUNT and not bool(cache_user['blocked']):
        cache.delete(user.id)
        cache.set(user.id, {'count':int(cache_user['count']),'last_date':cache_user['last_date'],'blocked':True,}, 86400*365)
    if int(cache_user['count']) > settings.ACTIVATION_COUNT and bool(cache_user['blocked']):
        time = datetime.datetime.now() - cache_user['last_date']
        if time.seconds > settings.BLOCKED_TIME:
            cache.delete(user.id)
            cache.set(user.id, {'count':0,'last_date':cache_user['last_date'],'blocked':False,}, 86400*365)
        else:
            return {
                    'redirect':'/',
                   }
            #HttpResponseRedirect('/index/')
    
    if request.method == 'POST':
        form = CardForm(request.POST)
        
        if form.is_valid():
            try:
                print form.cleaned_data['series'], form.cleaned_data['pin'], form.cleaned_data['card_id']
                #card = Card.objects.get(series=form.cleaned_data['series'], pin=form.cleaned_data['pin'], sold__isnull=False, start_date__lte=datetime.datetime.now(), end_date__gte=datetime.datetime.now(), activated__isnull=True)
                
                #card.activated=datetime.datetime.now()
                #card.activated_by = user
                #card.save()
                #summ = -card.nominal
                #type = TransactionType.objects.get(internal_name=u'ACTIVATION_CARD')
                #user.ballance = user.ballance-summ
                #user.save()
                #request.session['user'] = user
                #request.session.modified = True
                #transaction = Transaction(tarif=None, bill='', description = "", account=user, type=type, approved=True, summ=summ, created=datetime.datetime.now(), promise=False)
                #transaction.save()
                #cache.delete(user.id)
                #cache.add(user.id, {'count':0,'last_date':cache_user['last_date'],'blocked':False,})
                #return HttpResponseRedirect('/index/')
                connection_server = Pyro.core.getProxyForURI("PYROLOC://%s:7766/rpc" % unicode(settings.RPC_ADDRESS))
                import hashlib
                md1 = hashlib.md5(settings.RPC_PASSWORD)
                md1.hexdigest()
               
                password = str(md1.hexdigest())
                connection_server._setNewConnectionValidator(antiMungeValidator())
                connection_server._setIdentification("%s:%s:2" % (str(settings.RPC_USER), str(password)))

                res = connection_server.activate_pay_card(user.id, form.cleaned_data['series'], form.cleaned_data['card_id'], form.cleaned_data['pin'])
                print "res=", res

                if res == 'CARD_NOT_FOUND':
                    error_message = u'Ошибка активации. Карта не найдена.'
                elif res == 'CARD_NOT_SOLD':
                    error_message = u'Ошибка активации. Карта не была продана.'
                elif res == 'CARD_ALREADY_ACTIVATED':
                    error_message = u'Ошибка активации. Карта была активирована раньше.'
                elif res == 'CARD_EXPIRED':
                    error_message = u'Ошибка активации. Срок действия карты истёк.'
                elif res == 'CARD_ACTIVATED':
                    error_message = u'Карта успешно активирована.'
                elif res == 'CARD_ACTIVATION_ERROR':
                    error_message = u'Ошибка активации карты.'
            except Exception, e: 
                print e
            #if int(cache_user['count']) <= settings.ACTIVATION_COUNT:
            #    cache.delete(user.id)
            #    count = int(int(cache_user['count']))
            #    cache.set(user.id, {'count':count+1,'last_date':cache_user['last_date'],'blocked':False,}, 86400*365)
            #form = CardForm(request.POST)
            return {
                    'error_message':error_message,
                    #'form': form,
                    }
        else:
            #count = int(cache_user['count'])
            #if int(cache_user['count']) < settings.ACTIVATION_COUNT+1:
            #    cache.delete(user.id)
            #    cache.add(user.id, {'count':count+1,'last_date':cache_user['last_date'],'blocked':False,})
            return {
                    'error_message': u"Проверьте заполнение формы",
                    #'form': form,
                    }            
    else:
        #form = CardForm()
        return {
                'error_message': u"Ошибка активации карточки",
                #'form':form,
                }

@render_to('accounts/account_prepays_traffic.html')
def account_prepays_traffic(request):
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    user = request.session['user']
    try:
        from billservice.models import AccountPrepaysTrafic, PrepaidTraffic
        account_tariff = AccountTarif.objects.get(account=user, datetime__lt=datetime.datetime.now())[:1]
        account_prepays_trafic = AccountPrepaysTrafic.objects.filter(account_tarif=account_tariff)
        prepaidtraffic = PrepaidTraffic.objects.filter(id__in=[ i.prepaid_traffic.id for i in account_prepays_trafic])
    except:
        prepaidtraffic = None
        account_tariff = None  
    return {
            'prepaidtraffic':prepaidtraffic,
            'account_tariff':account_tariff,
            }
    

class antiMungeValidator(Pyro.protocol.DefaultConnValidator):
    def __init__(self):
        Pyro.protocol.DefaultConnValidator.__init__(self)
    def createAuthToken(self, authid, challenge, peeraddr, URI, daemon):
        return authid
    def mungeIdent(self, ident):
        return ident
    
    
def client(request):
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    user = request.session['user']
    # CONNECTION TO RCP SERVER
    try:
        connection = Pyro.core.getProxyForURI("PYROLOC://%s:7766/rpc" % unicode(settings.RPC_ADDRESS))
        import hashlib
        md1 = hashlib.md5(settings.RPC_PASSWORD)
        md1.hexdigest()
       
        password = str(md1.hexdigest())
        connection._setNewConnectionValidator(antiMungeValidator())
        print connection._setIdentification("%s:%s:2" % (str(settings.RPC_USER), str(password)))
        connection.test()
    except Exception, e:
        if isinstance(e, Pyro.errors.ConnectionDeniedError):
            error_message = u"Отказано в авторизации."
        else:
            error_message  = u"Невозможно подключиться к серверу."
    # create image
    from django.http import HttpResponse
    t1 = datetime.timedelta(days = 30)
    a1 = datetime.datetime.now() - t1
    a2 = datetime.datetime.now()
    cargs = ('gstat_multi', a1, a2)
    #for traffic_class in TrafficClass.objects.all().order_by('weight'):
    #    min_weight = traffic_class
    ckwargs = {'return':{}, 'options':{'autoticks':False, 'antialias':True}, 'dcname': 'nfs_web', 'speed':True, 'by_col':'classes', 'users':[user.id], 'classes':[i.id for i in TrafficClass.objects.all()]}
    imgs = connection.makeChart(*cargs, **ckwargs)
    response = HttpResponse(imgs, content_type='image/png')
    return response
            

@render_to('accounts/traffic_limit.html')        
def traffic_limit(request):
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    user = request.session['user']
    cursor = connection.cursor()
    cursor.execute("""SELECT id FROM billservice_tariff WHERE id=get_tarif(%s)""" % (user.id)) 
    
    try:
        tariff = cursor.fetchone()[0]
        #tariff = Tariff.objects.get(id=tariff)
        traffic = TrafficLimit.objects.filter(tarif=tariff) 
    except:
        traffic = None
    return {
            'trafficlimit':traffic,
            'user':user,
            } 
            
            
@render_to('accounts/statistics.html')
def statistics(request):
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    user = request.session['user']
    net_flow_streams = NetFlowStream.objects.filter(account=user).order_by('-date_start')[:8]
    transaction = Transaction.objects.filter(account=user).order_by('-created')[:8]
    active_session = ActiveSession.objects.filter(account=user).order_by('-date_start')[:8]
    services = AccountAddonService.objects.filter(account=user).order_by('-activated')[:8]  
    return {
            'net_flow_stream':net_flow_streams,
            'transactions':transaction,
            'active_session':active_session,
            'services':services,
            }


@render_to('accounts/addonservice.html')
def addon_service(request):
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    user = request.session['user']
    
    cursor = connection.cursor()
    cursor.execute("""select tarif_id FROM billservice_accounttarif WHERE account_id=%s and datetime<now()  ORDER BY id DESC LIMIT 1""" % (user.id)) 
    account_tariff_id = cursor.fetchone()[0]
    
    services = AddonServiceTarif.objects.filter(tarif__id=account_tariff_id)
    user_services = AccountAddonService.objects.filter(account=user, deactivated__isnull=True)
    accountservices = []
    for uservice in user_services:
        if uservice.service.wyte_period_id:
            delta = settlement_period_info(uservice.activated, uservice.service.wyte_period.length_in, uservice.service.wyte_period.length)[2]
            print "delta=", delta, uservice.activated + datetime.timedelta(seconds = delta), datetime.datetime.now()
            if uservice.activated + datetime.timedelta(seconds = delta)>datetime.datetime.now():
                uservice.wyte = True
                print 11
                uservice.end_wyte_date = uservice.activated + datetime.timedelta(seconds = delta)
            else:
                print 33
                uservice.wyte = False
        elif uservice.service.wyte_cost:
            uservice.wyte = True
        else:
            uservice.wyte = False
            print 22
        accountservices.append(uservice)  
        
    user_services_id = [x.service.id for x in accountservices if not x.deactivated]
    services = services.exclude(service__id__in=user_services_id) 
    return_dict = {
                   'services':services,
                   'user_services':user_services,
                   'user':user,
                   }
    if request.session.has_key('service_message'):
        return_dict['service_message'] = request.session['service_message']
        del(request.session['service_message']) 
    return return_dict 
    
def service_action(request, action, id):
    
    """
    в случее set id являеться идентификатором добавляемой услуги
    в случее del id являеться идентификатором accountaddon_service 
    """
    
    if not request.session.has_key('user'):
        return HttpResponseRedirect('/')
    user = request.session['user']
    
    try:
        connection_server = Pyro.core.getProxyForURI("PYROLOC://%s:7766/rpc" % unicode(settings.RPC_ADDRESS))
        import hashlib
        md1 = hashlib.md5(settings.RPC_PASSWORD)
        md1.hexdigest()
       
        password = str(md1.hexdigest())
        connection_server._setNewConnectionValidator(antiMungeValidator())
        connection_server._setIdentification("%s:%s:2" % (str(settings.RPC_USER), str(password)))
        #connection_server.test()
    except Exception, e:
        if isinstance(e, Pyro.errors.ConnectionDeniedError):
            request.session['service_message'] = u"Ошибка при подключении к серверу"
            return HttpResponseRedirect('/services/')
        else:
            request.session['service_message']  = u"Нет связи с сервером. Обратитесь в службу поддержки"
            return HttpResponseRedirect('/services/')
        
    if action == u'set':
        print 123
        
        try:
            account_addon_service = AddonService.objects.get(id=id)
        except:
            request.session['service_message'] = u'Вы не можете подключить данную услугу'
            return HttpResponseRedirect('/services/')
        result = connection_server.add_addonservice(user.id, id)
        print result 
        if result == True:
            request.session['service_message'] = u'Услуга подключена'
            return HttpResponseRedirect('/services/')
        elif result == 'ACCOUNT_DOES_NOT_EXIST':
            request.session['service_message'] = u'Указанный пользователь не найден'
            return HttpResponseRedirect('/services/') 
        elif result == 'ADDON_SERVICE_DOES_NOT_EXIST':
            request.session['service_message'] = u'Указанныя подключаемая услуга не найдена'  
            return HttpResponseRedirect('/services/')   
        elif result == 'NOT_IN_PERIOD':
            request.session['service_message'] = u'Активация выбранной услуги в данный момент не доступна'  
            return HttpResponseRedirect('/services/') 
        elif result == 'ALERADY_HAVE_SPEED_SERVICE':
            request.session['service_message'] = u'У вас уже подключенны изменяющие скорость услуги'  
            return HttpResponseRedirect('/services/')  
        elif result == 'ACCOUNT_BLOCKED':
            request.session['service_message'] = u'Услуга не может быть подключена. Проверьте Ваш баланс или обратитесь в службу поддержки'  
            return HttpResponseRedirect('/services/') 
        elif result == 'ADDONSERVICE_TARIF_DOES_NOT_ALLOWED':
            request.session['service_message'] = u'На вашем тарифном плане активация выбранной услуги невозможна'  
            return HttpResponseRedirect('/services/')     
        elif result == 'TOO_MUCH_ACTIVATIONS':
            request.session['service_message'] = u'Превышенно допустимое количество активаций. Обратитесь в службу поддержки'  
            return HttpResponseRedirect('/services/') 
        elif result == 'SERVICE_ARE_ALREADY_ACTIVATED':
            request.session['service_message'] = u'Указанная услуга уже подключена и не может быть активирована дважды.'  
            return HttpResponseRedirect('/services/') 
        else:
            request.session['service_message'] = u'Услугу не возможно подключить'
            return HttpResponseRedirect('/services/')
    elif action == u'del':
        result = connection_server.del_addonservice(user.id, id)
        if result == True:
            request.session['service_message'] = u'Услуга отключена'
            return HttpResponseRedirect('/services/')
        elif result == 'ACCOUNT_DOES_NOT_EXIST':
            request.session['service_message'] = u'Указанный пользователь не найден'
            return HttpResponseRedirect('/services/') 
        elif result == 'ADDON_SERVICE_DOES_NOT_EXIST':
            request.session['service_message'] = u'Указанныя подключаемая услуга не найдена'  
            return HttpResponseRedirect('/services/')   
        elif result == 'ACCOUNT_ADDON_SERVICE_DOES_NOT_EXIST':
            request.session['service_message'] = u'Вы не можите отключить выбранную услугу'  
            return HttpResponseRedirect('/services/') 
        elif result == 'NO_CANCEL_SUBSCRIPTION':
            request.session['service_message'] = u'Даннная услуга не может быть отключена. Обратитесь в службу поддержки'  
            return HttpResponseRedirect('/services/')  
        else:
            request.session['service_message'] = u'Услугу не возможно отключить'
            return HttpResponseRedirect('/services/')
    else:
        request.session['service_message'] = u'Невозможно совершить действие'
        return HttpResponseRedirect('/services/')
          
    




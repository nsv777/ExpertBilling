# -*-coding: utf-8 -*-

from ebscab.lib.decorators import render_to, ajax_request
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django_tables2_reports.config import RequestConfigReport as RequestConfig
from django_tables2_reports.utils import create_report_http_response
from object_log.models import LogItem

from tables import SettlementPeriodTable

from billservice.forms import SettlementPeriodForm
from billservice.models import SettlementPeriod
import datetime
from django.contrib import messages
log = LogItem.objects.log_action



@login_required
@render_to('ebsadmin/settlement_period_list.html')
def settlementperiod(request):
    res = SettlementPeriod.objects.all()
    table = SettlementPeriodTable(res)
    table_to_report = RequestConfig(request, paginate=True if not request.GET.get('paginate')=='False' else False).configure(table)
    if table_to_report:
        return create_report_http_response(table_to_report, request)
    return {"table": table} 
    
@login_required
@render_to('ebsadmin/settlement_period_edit.html')
def settlementperiod_edit(request):

    id = request.GET.get("id")
    item = None
    if request.method == 'POST': 
        if id:
            item = SettlementPeriod.objects.get(id=id)
            form = SettlementPeriodForm(request.POST, instance=item)
        else:
             form = SettlementPeriodForm(request.POST)
        if id:
            if  not (request.user.is_staff==True and request.user.has_perm('billservice.change_settlementperiod')):
                return {'status':False, 'message': u'У вас нет прав на редактирование расчётных периодов'}
            
        if  not (request.user.is_staff==True and request.user.has_perm('billservice.add_settlementperiod')):
            return {'status':False, 'message': u'У вас нет прав на добавление расчётных периодов'}

        
        if form.is_valid():
 
            model = form.save(commit=False)
            model.save()
            log('EDIT', request.user, model) if id else log('CREATE', request.user, model) 
            messages.success(request, u'Расчётный период удачно создан.', extra_tags='alert-success')
            return HttpResponseRedirect(reverse("settlementperiod"))
        else:
            messages.warning(request, u'Ошибка.', extra_tags='alert-danger')
            return {'form':form,  'status': False, 'item':item} 
    else:
        id = request.GET.get("id")

        if id:
            if  not (request.user.is_staff==True and request.user.has_perm('billservice.settlementperiod_view')):
                return {'status':True}

            item = SettlementPeriod.objects.get(id=id)
            form = SettlementPeriodForm(instance=item)
        else:
            form = SettlementPeriodForm(initial={'time_start':datetime.datetime(2010,1,1,0,0,0)})
            
   
    return { 'form':form, 'item': item} 

@ajax_request
@login_required
def settlementperiod_delete(request):
    if  not (request.user.is_staff==True and request.user.has_perm('billservice.delete_settlementperiod')):
        return {'status':False, 'message': u'У вас нет прав на удаление расчётных периодов'}
    id = int(request.POST.get('id',0)) or int(request.GET.get('id',0))
    if id:
        try:
            item = SettlementPeriod.objects.get(id=id)
        except Exception, e:
            return {"status": False, "message": u"Указанный расчётный период не найден %s" % str(e)}
        log('DELETE', request.user, item)
        item.delete()
        return {"status": True}
    else:
        return {"status": False, "message": "SettlementPeriod not found"} 
    
    
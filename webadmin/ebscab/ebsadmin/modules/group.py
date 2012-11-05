# -*-coding: utf-8 -*-

from ebscab.lib.decorators import render_to, ajax_request
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django_tables2_reports.config import RequestConfigReport as RequestConfig
from django_tables2_reports.utils import create_report_http_response
from object_log.models import LogItem

from ebsadmin.tables import GroupTable

from billservice.forms import GroupForm
from billservice.models import Group

log = LogItem.objects.log_action



@login_required
@render_to('ebsadmin/group_list.html')
def group(request):
    res = Group.objects.all()
    table = GroupTable(res)
    table_to_report = RequestConfig(request, paginate=False).configure(table)
    if table_to_report:
        return create_report_http_response(table_to_report, request)
            
    return {"table": table} 
    
@login_required
@render_to('ebsadmin/group_edit.html')
def group_edit(request):
    id = request.POST.get("id")

    item = None

    if request.method == 'POST': 

        if id:
            model = Group.objects.get(id=id)
            form = GroupForm(request.POST, instance=model) 
            if  not (request.user.is_staff==True and request.user.has_perm('billservice.change_group')):
                return {'status':False, 'message': u'У вас нет прав на редактирование групп трафика'}
        else:
            form = GroupForm(request.POST) 
        if  not (request.user.is_staff==True and request.user.has_perm('billservice.add_group')):
            return {'status':False, 'message': u'У вас нет прав на добавление групп трафика'}

        if form.is_valid():
 
            model = form.save(commit=False)
            model.save()
            log('EDIT', request.user, model) if id else log('CREATE', request.user, model) 
            return HttpResponseRedirect(reverse("group"))
        else:
            print form._errors
            return {'form':form,  'status': False} 

    else:
        id = request.GET.get("id")

        if id:
            if  not (request.user.is_staff==True and request.user.has_perm('billservice.group_view')):
                return {'status':True}

            item = Group.objects.get(id=id)
            
            form = GroupForm(instance=item)
        else:
            form = GroupForm()

    return { 'form':form, 'status': False} 

@ajax_request
@login_required
def group_delete(request):
    if  not (request.user.is_staff==True and request.user.has_perm('billservice.delete_group')):
        return {'status':False, 'message': u'У вас нет прав на удаление оборудования'}
    id = int(request.POST.get('id',0)) or int(request.GET.get('id',0))
    if id:
        try:
            item = Group.objects.get(id=id)
        except Exception, e:
            return {"status": False, "message": u"Указанное оборудование не найдено %s" % str(e)}
        log('DELETE', request.user, item)
        item.delete()
        return {"status": True}
    else:
        return {"status": False, "message": "Hardware not found"} 
    
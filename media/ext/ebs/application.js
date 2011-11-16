Ext.onReady(function(){
    //Ext.app.REMOTING_API.enableBuffer = 100;
    Ext.ns('EBS');

    EBS.messages = {
        fadeSpeed: 250,
        fadeInterval:4000
    };
    
    EBS.base = {}; // Base components

    EBS.menu = [];

    // Datastore
    EBS.store = {};
    // Datastore field/type mapping
    EBS.reader = {};
    EBS.writer = {};
    

    EBS.topToolbar = [];
    EBS.bottomToolbar = [];
    EBS.forms = {}; // для форм из компонент
    EBS.windows = {};
    EBS.windows.keys =[];
    EBS.conponents = {};
    EBS.conponents.keys =[];

    // hide debug info. TODO: remove at production
    if(typeof(console) != "object"){
        var console = new (function(){
                this.log=function(){};
                this.info=this.log;
                this.trace=this.log
            })()
    }

    EBS.closeForm = function(self){
        winCmp = self.ownerCt.ownerCt;
        winCmp.hide().destroy();
        delete EBS.windows[winCmp.id];
    }
    EBS.displayForm = function(xtype, action, self){
        /*
         * Вызывается из меню компоненты
         *
         * создает форму
         *
         **/

           console.log(action, self);

            //Create edit window
           selection = self.selModel.selections;
           if(selection.items.length!=1){
               Ext.Msg.alert(i18n.information,i18n.please_select_one_row);
               return;
            }
           rec = selection.items[0];
           form = 'EBS.forms.'+xtype+'.'+action;
           window_key =  xtype+'_'+action;
           form_data = eval(form);
           form_callback = eval(form+'_submitAction');

           //if(typeof form_callback != "function")
           //    Ext.Msg.alert('Error: callback function is not accessible', form + '_submitAction ');

           //if(!EBS.windows[window_key]){
           winCmp = Ext.get(window_key);
           if(!winCmp){
                        winCmp = new Ext.Window({
                            id:window_key,
                            applyTo:Ext.get('body'),
                            width:500,
                            height:300,
                            title:form_data.windowTitle,
                            autoHeight: true,
                            viewConfig: {
                                forceFit: true
                            },
                            tools : [{
                                    id: 'gear',
                                    handler: function() {
                                        Ext.Msg.alert('TODO:','Attach as tab.');
                                        }
                                   }],

                            plain: true,
                            items: [form_data],
                            buttons: [{
                                    text:'Submit',
                                    handler: function(obj, e){
                                        form_callback(obj, e);
                                        form = this.ownerCt.ownerCt.items.items[0].getForm()
                                        form.updateRecord(form.rec);
                                        //Update server data
                                        //form.rec.store.save();
                                        EBS.closeForm(this)
                                    }
                                },{
                                    text: 'Close',
                                    handler: function(){
                                        EBS.closeForm(this)
                                    }
                                }]
                        });
                        EBS.windows[window_key] = winCmp;
                    }
             form = winCmp.items.items[0].getForm();
             form.rec = selection.items[0];

             //form.loadRecord(form.rec);
             //form.load({url:'/account/', method:'GET',params:{'id':selection.items[0].id}} );
             winCmp.show();
    }

    EBS.displayCustomForm = function(xtype, action, self){
        /*
         * Вызывается из меню компоненты
         *
         * создает форму
         *
         **/
    	   //alert(123);
           console.log(action, self);

            //Create edit window
           selection = self.selModel.selections;
           if(selection.items.length!=1){
               Ext.Msg.alert(i18n.information,i18n.please_select_one_row);
               return;
            }
           rec = selection.items[0];
           //alert(rec.id);
           form = 'EBS.forms.'+xtype+'.'+action;
           //alert(form);
           window_key =  xtype+'_'+action;
           //alert(window_key);
           form_data = eval(form);
           form_callback = eval(form+'_submitAction');

           //alert(form_data.windowTitle);
           //if(typeof form_callback != "function")
           //    Ext.Msg.alert('Error: callback function is not accessible', form + '_submitAction ');

           //if(!EBS.windows[window_key]){
           winCmp = Ext.get(window_key);
           if(!winCmp){
                        winCmp = new Ext.Window({
                            id:window_key,
                            applyTo:Ext.get('body'),
                            //width:500,
                            //height:300,
                            layout:'anchor',
                            title:form_data.windowTitle,
                            autoHeight: false,
                            viewConfig: {
                                forceFit: true
                            },
                            

                            plain: true,
                            items: [form_data],
                        });
                        EBS.windows[window_key] = winCmp;
                    }
             //form = winCmp.items.items[0].getForm();
             //form.rec = selection.items[0];

             //form.loadRecord(form.rec);
             //form.load({url:'/account/', method:'GET',params:{'id':selection.items[0].id}} );
             winCmp.show();
    }
    
    EBS.displayFormInTab = function(xtype, action, id, self){
        /*
         * Вызывается из меню компоненты
         *
         * создает форму
         *
         **/

           console.log(action, self);

            //Create edit window
           /*selection = self.selModel.selections;
           if(selection.items.length!=1){
               Ext.Msg.alert(i18n.information,i18n.please_select_one_row);
               return;
            }
           rec = selection.items[0];*/
           form = 'EBS.forms.'+xtype+'.'+action;
           window_key =  xtype+'_'+action;
           form_data = eval(form);
           form_callback = eval(form+'_submitAction');

           //if(typeof form_callback != "function")
           //    Ext.Msg.alert('Error: callback function is not accessible', form + '_submitAction ');

           //if(!EBS.windows[window_key]){
           winCmp = Ext.get(window_key);

           //if(!winCmp){
           if(true){
                        winCmp = new Ext.Panel({
                            id:window_key+id,
                            instance_id:id,
                            applyTo:Ext.get('body'),
                            //width:500,
                            //height:300,
                            title:form_data.windowTitle,
                            autoHeight: false,
                            viewConfig: {
                                forceFit: true
                            },
                            tools : [{
                                    id: 'gear',
                                    handler: function() {
                                        Ext.Msg.alert('TODO:','Attach as tab.');
                                        }
                                   }],

                            plain: true,
                            items: [form_data],

                        });
                        EBS.windows[window_key] = winCmp;
                    }
           	 if(id){
           		 form = winCmp.items.items[0].items.items[0].items.items[0].getForm();
           		 //form.rec = selection.items[0];
           		 //alert(form.url);
           		 form.load({url:form.url,method:form.method,params:{'id':id}});
           		 //form.loadRecord(form.rec);
           	 };
             EBS.windowCmp.add(winCmp)
             //winCmp.show();
    }

    EBS.displayFormInSpecTab = function(xtype, action, ids, tab, self){
        /*
         * Вызывается из меню компоненты
         *
         * создает форму
         *
         **/

           console.log(action, self);
           var id, account_id;
           id=ids.id;
           account_id=ids.account_id;
            //Create edit window
           /*selection = self.selModel.selections;
           if(selection.items.length!=1){
               Ext.Msg.alert(i18n.information,i18n.please_select_one_row);
               return;
            }
           rec = selection.items[0];*/
           form = 'EBS.forms.'+xtype+'.'+action;
           window_key =  xtype+'_'+action;
           form_data = eval(form);
           form_callback = eval(form+'_submitAction');

           //if(typeof form_callback != "function")
           //    Ext.Msg.alert('Error: callback function is not accessible', form + '_submitAction ');

           //if(!EBS.windows[window_key]){
           winCmp = Ext.get(window_key);

           //if(!winCmp){
           if(true){
                        winCmp = new Ext.Panel({
                            id:window_key+id,
                            instance_id:id,
                            parent_id:account_id,
                            applyTo:Ext.get('body'),
                            //width:500,
                            //height:1200,
                            //layout:'fit',
                            title:form_data.windowTitle,
                            closable:true,
                            //autoHeight: true,
                            autoHeight: true,
                            //viewConfig: {
                            //    forceFit: true
                            //},
                            tools : [{
                                    id: 'gear',
                                    handler: function() {
                                        Ext.Msg.alert('TODO:','Attach as tab.');
                                        }
                                   }],

                            plain: true,
                            items: [form_data],
                            buttons: [{
                                    text:'Submit',
                                    handler: function(obj, e){
                                        form_callback(obj, e);
                                        form = this.ownerCt.ownerCt.items.items[0].getForm()
                                        form.submit({url:form.save_url, waitMsg:'Saving Data...', submitEmptyText: true});
                                        //Update server data
                                        //form.rec.store.save();
                                        //EBS.closeForm(this)
                                    }
                                },{
                                    text: 'Close',
                                    handler: function(){
                                        EBS.closeForm(this)
                                    }
                                }]
                        });
                        EBS.windows[window_key] = winCmp;
                    }
             form = winCmp.items.items[0].getForm();
             //form.rec = selection.items[0];
             //alert(form.url);
             if (id){
            	 form.load({url:form.url,method:form.method,params:{'id':id}});
             };
             //form.loadRecord(form.rec);
             
             tab.add(winCmp)
             //winCmp.show();
    }

    
    
    EBS.displayWindow = function(xtype, params){
        /*
         * !!!Претендент на удаление!!!
         *
         * Вызывается из меню компоненты
         *
         * создает форму
         *
         * params = {action:action, self:self, selection:self.selModel.selections}
         **/
            //console.log(xtype, params)
    }

    //load menu
    var treePanel = new Ext.tree.TreePanel({
      id: 'tree-panel',
      //title: 'Sample Layouts',
        region:'north',
        split: true,
        //minSize: 150,
        autoScroll: true,
        autoHeight: true,
        // tree-specific configs:
        rootVisible: false,
        lines: true,
        singleExpand: false,
        useArrows: true,
        root: new Ext.tree.AsyncTreeNode({
            text: "Root",
            expanded: true,
            children: mainMenu
        }),
        listeners: {
                'click' : function(n){
                                    // get selected node
                                    var sn = this.selModel.selNode || {};
                                    if(n.leaf){ //&& n.id != sn.id
                                        var type = n.attributes.type;
                                        //console.info(n.id+'Grid',this,arguments, type);

                                        var type_exists = false;
                                        for(i=0;i<EBS.windows.keys.length;i++){
                                            if(EBS.windows.keys[i]==type){
                                                type_exists = true;
                                                break;
                                            }
                                        }
                                            /*  Если объект = синглетон:
                                             *  проверяется - создано ли уже такое окно
                                             *  если да- открывается, иначе создается новый компонент
                                             *
                                             *  у синглетона присутствует атрибут id. по нему делается проверка.
                                             *
                                             *TODO: Перенести в конструктор, где он и должен быть. проблема - инициализация.
                                             **/
                                        if(type_exists){
                                            if(n.attributes.singleton){
                                                if(EBS.windowCmp.items.containsKey(type)){
                                                    EBS.windowCmp.activate(type);
                                                }else{
                                                    cmp = Ext.create({
                                                        xtype:type,
                                                        id:type,
                                                        singleton:true
                                                        });
                                                    EBS.windowCmp.add(cmp);
                                                }
                                            }else{
                                                cmp = Ext.create({
                                                    xtype:type
                                                    });
                                                EBS.windowCmp.add(cmp);
                                            }

                                        }

                                    }
                        }
        }
    });



    EBS.base = function(){
        Ext.QuickTips.init();
        Ext.state.Manager.setProvider(new  Ext.state.CookieProvider());

        Ext.Direct.on('message', function(e){
            if(console && console.log)
                console.log(String.format('<p><i>{0}</i></p>', e.data));
        });


        return {
            window: {},
            init: function(){
                        // initialize datastore
                        //EBS.store.accounts.load()
                        //EOF initialize datastore

                        //tabScrollerMenu =

                       //EBS.viewport =
                        new Ext.Viewport({
                            layout:'border',
                            //   renderTo:Ext.getBody(),
                            items:[
                            //Header
                                {
                                    height  : 100,
                                    id      : 'header',
                                    baseCls : 'header-line',
                                    region  :'north',
                                    html    : '<div class="user_block f-right"><span class="sustem_user">' + EBS.store.logged_user.username + '</span> <span class="exit"><a href="/helpdesk/logout/">'+i18n.logout+'</a></span></div>',
                                    border  :false,
                                    margins : '0 0 5 0'
                                },

                            // tab panel
                                {
                                    xtype   : 'panel',
                                    id      : 'center_panel',
                                    region  : 'center',
                                    height  : 200,
                                    width   : 400,
                                    layout  : 'fit',
                                    //title  : 'Exercising scrollable tabs with a tabscroller menu',
                                    items   : {
                                        xtype           : 'tabpanel',
                                        activeTab       : 0,
                                        id              : 'main_tab_panel',
                                        stateful: true,
                                        stateId: 'main_tab_panel',
                                        enableTabScroll : true,
                                        resizeTabs      : true,
                                        minTabWidth     : 75,
                                        border          : false,
                                        defaults		: {               // defaults are applied to items, not the container
                                            				closable:true,
                                            				autoScroll:true,
                                        				},
                                        plugins         : [ new Ext.ux.TabScrollerMenu({
                                                                                        maxText  : 15,
                                                                                        pageSize : 5
                                                                                        })
                                                         ],
                                        items           : [
                                            {
                                                title : 'Welcome',
                                                html  : i18n.welcomeText
                                            },
                                            
                                            {
                                                xtype:'ebs_nasPanel',
                                                id:'ebs_nasPanel'

                                            }
                                        ]
                                    }
                                },
                            // Right help block
                                {
                                    id:'help_menu',
                                    region: 'east',
                                    title: 'Title for Panel',
                                    collapsible: true,
                                    html: i18n.helpMenuInnerText,
                                    split: true,
                                    width: 100,
                                    minWidth: 100

                                },
                            // Main menu block
                                {
                                    id      :'main_menu',
                                    xtype   : 'panel',
                                    region  : 'west',
                                    title   : 'Title for Panel',
                                    //layout  : 'accordion',
                                    collapsible: false,
                                    split   : true,
                                    //width   : 180,
                                    minWidth: 180,
                                    items: [treePanel]
                                    /*items : [{
                                                title: 'Users',
                                                xtype: 'panel',
                                                //scale: 'large',
                                                iconAlign: 'top',
                                                cls: 'x-btn-as-arrow',
                                                items : [{
                                                  title: '123',
                                                  handler : function(){
                                                      cmp = new EBS.conponents.usersGrid();
                                                      Ext.getCmp('main_tab_panel').add(cmp);
                                                  }
                                                }]
                                                  
                                              }
                                    ]*/

                                }
                            ]
                        }); //new Ext.Viewport
                        EBS.windowCmp = Ext.getCmp('main_tab_panel');
            }
        }
    }();


   /*
    window frame template = {
        menu_block = EBS.const.USER
        menu_name = EBS.locale.users_accounts;
        menu_order
        title
        description
        help_menu = {} //west_block /// need to extend
        menu
        panel
        }
   */





    




/* BASE Components*/
    EBS.base.GridPanel = Ext.extend(Ext.grid.GridPanel, {
        constructor: function(config) {

               Ext.apply(this, {
                    bbar: new Ext.PagingToolbar({
                           pageSize: 100,
                          // store: this.store,
                           displayInfo: true,
                           dispalyMsg: i18n.paginatorDispalyMsg,
                           emptyMsg: i18n.paginatorEmptyMsg
                           //plugins: [new Ext.ux.SlidingPager(), this.filters],
                        }),
                    selModel : new Ext.grid.RowSelectionModel({
                         singleSelect : true
                            })
                
                });
             EBS.base.GridPanel.superclass.constructor.call(this, config)
        },
        initComponent: function(arguments) {
            EBS.base.GridPanel.superclass.initComponent.apply(this, arguments);
        }



    });
    Ext.reg("ebs_base_grid", EBS.base.GridPanel);
    Ext.exampledata = [
                              ['AL', 'Alabama', 'The Heart of Dixie'],
                              ['AK', 'Alaska', 'The Land of the Midnight Sun'],
                              ['AZ', 'Arizona', 'The Grand Canyon State'],
                              ['AR', 'Arkansas', 'The Natural State'],
                              ['CA', 'California', 'The Golden State'],
                              ['CO', 'Colorado', 'The Mountain State'],
                              ['CT', 'Connecticut', 'The Constitution State'],
                              ['DE', 'Delaware', 'The First State'],
                              ['DC', 'District of Columbia', "The Nation's Capital"],
                              ['FL', 'Florida', 'The Sunshine State'],
                              ['GA', 'Georgia', 'The Peach State'],
                              ['HI', 'Hawaii', 'The Aloha State'],
                              ['ID', 'Idaho', 'Famous Potatoes'],
                              ['IL', 'Illinois', 'The Prairie State'],
                              ['IN', 'Indiana', 'The Hospitality State'],
                              ['IA', 'Iowa', 'The Corn State'],
                              ['KS', 'Kansas', 'The Sunflower State'],
                              ['KY', 'Kentucky', 'The Bluegrass State'],
                              ['LA', 'Louisiana', 'The Bayou State'],
                              ['ME', 'Maine', 'The Pine Tree State'],
                              ['MD', 'Maryland', 'Chesapeake State'],
                              ['MA', 'Massachusetts', 'The Spirit of America'],
                              ['MI', 'Michigan', 'Great Lakes State'],
                              ['MN', 'Minnesota', 'North Star State'],
                              ['MS', 'Mississippi', 'Magnolia State'],
                              ['MO', 'Missouri', 'Show Me State'],
                              ['MT', 'Montana', 'Big Sky Country'],
                              ['NE', 'Nebraska', 'Beef State'],
                              ['NV', 'Nevada', 'Silver State'],
                              ['NH', 'New Hampshire', 'Granite State'],
                              ['NJ', 'New Jersey', 'Garden State'],
                              ['NM', 'New Mexico', 'Land of Enchantment'],
                              ['NY', 'New York', 'Empire State'],
                              ['NC', 'North Carolina', 'First in Freedom'],
                              ['ND', 'North Dakota', 'Peace Garden State'],
                              ['OH', 'Ohio', 'The Heart of it All'],
                              ['OK', 'Oklahoma', 'Oklahoma is OK'],
                              ['OR', 'Oregon', 'Pacific Wonderland'],
                              ['PA', 'Pennsylvania', 'Keystone State'],
                              ['RI', 'Rhode Island', 'Ocean State'],
                              ['SC', 'South Carolina', 'Nothing Could be Finer'],
                              ['SD', 'South Dakota', 'Great Faces, Great Places'],
                              ['TN', 'Tennessee', 'Volunteer State'],
                              ['TX', 'Texas', 'Lone Star State'],
                              ['UT', 'Utah', 'Salt Lake State'],
                              ['VT', 'Vermont', 'Green Mountain State'],
                              ['VA', 'Virginia', 'Mother of States'],
                              ['WA', 'Washington', 'Green Tree State'],
                              ['WV', 'West Virginia', 'Mountain State'],
                              ['WI', 'Wisconsin', "America's Dairyland"],
                              ['WY', 'Wyoming', 'Like No Place on Earth']
                          ];
    EBS.base.BoxSelect =Ext.extend(Ext.ux.BoxSelect,{
    	constructor: function(config) {
    		
            Ext.apply(this, {
				fieldLabel: 'State',
				resizable: true,
				name: 'to[]',
				anchor:'100%',
				store: new Ext.data.SimpleStore({
					fields: ['abbr', 'state', 'nick'],
					data: Ext.exampledata,
					sortInfo: {field: 'state', direction: 'ASC'}
				}),
				mode: 'local',
				displayField: 'state',
				displayFieldTpl: '{state} ({abbr})',
				valueField: 'abbr',
				addUniqueValues: false,
				
            
            }
            );
            Ext.apply(this, Ext.applyIf(this.initialConfig, config));
            EBS.base.BoxSelect.superclass.constructor.call(this, config)
        },
        initComponent: function(arguments) {
            EBS.base.BoxSelect.superclass.initComponent.apply(this, arguments);
        }



    });
    Ext.reg("xboxselect", EBS.base.BoxSelect);
    
    EBS.AccountsPanel = Ext.extend(Ext.TabPanel, {
        initComponent:function() {
           var config = {
						title:'Аккаунты',
						id:'accountspanel',
						items:[{
						       xtype:'container',
						       title:'Поиск',
						       items:[{
						    	   

								    xtype: 'form',
								    autoHeight: true,
								    autoScroll: true,
								    autoWidth: true,
								    width: 907,
								    activeItem: 0,
								    layout: 'accordion',
								    bodyStyle: 'padding:15px',
								    items: [
								        {
								            xtype: 'fieldset',
								            autoHeight: true,
								            width: 888,
								            title: 'Учётные данные',
								            labelPad: 10,
								            labelWidth: 200,
								            items: [
								                {
								                    xtype: 'textfield',
								                    name: 'contract',
								                    anchor: '100%',
								                    fieldLabel: 'Номер договора'
								                },
								                {
								                    xtype: 'textfield',
								                    name: 'username',
								                    anchor: '100%',
								                    fieldLabel: 'Имя пользоателя'
								                },
								                {
								                    xtype: 'textfield',
								                    name: 'fullname',
								                    anchor: '100%',
								                    fieldLabel: 'ФИО'
								                },
								                {
								                    xtype: 'textfield',
								                    name: 'contactperson',
								                    anchor: '100%',
								                    fieldLabel: 'Контактное лицо'
								                },
								                {
								                    xtype: 'xcombocity',
								                    name: 'city',
								                    anchor: '100%',
								                    fieldLabel: 'Город',
								                    listeners:{
                                                    	select: function(combo, record, index) {
                                                    		
                                                    		this.findParentByType('form').getForm().findField('street').clearValue();
															this.findParentByType('form').getForm().findField('street').store.load({params:{city_id: this.value}});
                                                    		
                                                          },
                                                   },
								                },
								                {
								                    xtype: 'xcombostreet',
								                    name: 'street',
								                    anchor: '100%',
								                    fieldLabel: 'Улица',
								                    listeners:{
                                                    	select: function(combo, record, index) {
                                                    		
                                                    		this.findParentByType('form').getForm().findField("house").clearValue();
															this.findParentByType('form').getForm().findField("house").store.load({params:{street_id: this.value}});                                                                              },
                                                   

                                                    },
								                    	
								                },
								                {
								                    xtype: 'xcombohouse',
								                    name: 'house',
								                    anchor: '100%',
								                    fieldLabel: 'Дом',
								                    
								                },
								                {
								                    xtype: 'textfield',
								                    name: 'house_bulk',
								                    anchor: '100%',
								                    fieldLabel: 'Подъезд'
								                },
								                {
								                    xtype: 'textfield',
								                    name: 'room',
								                    fieldLabel: 'Квартира'
								                }
								            ]
								        },
								        {
								            xtype: 'fieldset',
								            autoHeight: true,
								            width: 889,
								            title: 'Тарификация',
								            items: [
								                {
								                    xtype: 'compositefield',
								                    anchor: '100%',
								                    fieldLabel: 'Баланс',
								                    items: [
								                        {
								                            xtype: 'combo',
								                            name: 'ballance_exp'
								                        },
								                        {
								                            xtype: 'textfield',
								                            name: 'ballance',
								                            fieldLabel: 'Label'
								                        }
								                    ]
								                },
								                {
								                    xtype: 'compositefield',
								                    anchor: '100%',
								                    fieldLabel: 'Кредит',
								                    items: [
								                        {
								                            xtype: 'combo',
								                            name: 'credit_exp'
								                        },
								                        {
								                            xtype: 'textfield',
								                            name: 'credit',
								                            fieldLabel: 'Label'
								                        }
								                    ]
								                },
								                {
								                    xtype: 'listview',
								                    multiSelect: true,
								                    columnResize: false,
								                    autoWidth:true,
								                    height:200,
								                    store: new Ext.data.JsonStore({
								                        paramsAsHash: true,
								                        autoLoad: {},
								                        proxy: new Ext.data.HttpProxy({
								                            url: '/ebsadmin/tariffs/',
								                            method:'GET',
								                        }),    
								                        fields: ['id', 'name'],
								                        root: 'records',
								                        remoteSort:true,
								                        
								                      }
								                    ),
								                    fieldLabel: 'Тарифные планы',
								                    columns: [
								                        {
								                            xtype: 'lvcolumn',
								                            header: 'Тарифный план',
								                            dataIndex:'name',
								                            //width: 0.25
								                        }
								                    ]
								                },
								                {
								                    xtype: 'listview',
								                    multiSelect: true,
								                    columnResize: false,
								                    autoWidth:true,
								                    fieldLabel: 'Группа',
								                    columns: [
								                        {
								                            xtype: 'lvcolumn',
								                            header: 'Column',
								                            //width: 0.25
								                        },
								                        {
								                            xtype: 'lvbooleancolumn',
								                            header: 'True/False'
								                        }
								                    ]
								                },
								                {
								                    xtype: 'checkbox',
								                    name: 'without_tariff',
								                    boxLabel: 'Да',
								                    anchor: '100%',
								                    fieldLabel: 'Блокировка по балансу'
								                },
								                {
								                    xtype: 'checkbox',
								                    boxLabel: 'BoxLabel',
								                    anchor: '100%',
								                    fieldLabel: 'Блокировка по балансу'
								                },
								                {
								                    xtype: 'checkbox',
								                    boxLabel: 'BoxLabel',
								                    anchor: '100%',
								                    fieldLabel: 'Блокировка по балансу'
								                }
								            ]
								        },
								        {
								            xtype: 'fieldset',
								            autoHeight: true,
								            width: 891,
								            title: 'Другое',
								            items: [
								                {
								                    xtype: 'listview',
								                    name:'nas_filter',
								                    id:'nas_filter',
								                    multiSelect: true,
								                    columnResize: false,
								                    fieldLabel: 'Сервер доступа',
								                    multiSelect: true,
								                    columnResize: false,
								                    autoWidth:true,
								                    autoHeight: true,
								                    maxHeight:200,
								                    border:true,
								                    store: new Ext.data.JsonStore({
								                        paramsAsHash: true,
								                        autoLoad: {},
								                        proxy: new Ext.data.HttpProxy({
								                            url: '/ebsadmin/nasses/',
								                            method:'GET',
								                        }),    
								                        fields: ['id', 'name'],
								                        root: 'records',
								                        remoteSort:true,
								                        
								                      }
								                    ),
								                    fieldLabel: 'Сервер доступа',
								                    columns: [
								                        {
								                            xtype: 'lvcolumn',
								                            header: 'Сервер доступа',
								                            dataIndex:'name',
								                            //width: 0.25
								                        }
								                    ]
								                },
								                {
								                    xtype: 'checkboxgroup',
								                    anchor: '100%',
								                    fieldLabel: 'IPN статусы',
								                    items: [
								                        {
								                            xtype: 'checkbox',
								                            name: 'ipn_added',
								                            boxLabel: 'Добавлен'
								                        },
								                        {
								                            xtype: 'checkbox',
								                            name: 'ipn_enabled',
								                            boxLabel: 'Активен'
								                        },
								                        {
								                            xtype: 'checkbox',
								                            name: 'ipn_sleep',
								                            boxLabel: 'Не менять статус'
								                        }
								                    ]
								                },
								                {
								                	xtype: 'listview',
								                    name:'systemuser_filter',
								                    id:'systemuser_filter',
								                    multiSelect: true,
								                    columnResize: false,
								                    fieldLabel: 'Менеджер',
								                    xtype: 'listview',
								                    multiSelect: true,
								                    columnResize: false,
								                    autoWidth:true,
								                    autoHeight: true,
								                    maxHeight:200,
								                    store: new Ext.data.JsonStore({
								                        paramsAsHash: true,
								                        autoLoad: {},
								                        proxy: new Ext.data.HttpProxy({
								                            url: '/ebsadmin/systemuser/',
								                            method:'GET',
								                        }),    
								                        fields: ['id', 'name'],
								                        root: 'records',
								                        remoteSort:true,
								                        
								                      }
								                    ),
								                    fieldLabel: 'Менеджер',
								                    columns: [
								                        {
								                            xtype: 'lvcolumn',
								                            header: 'Менеджер/Администратор',
								                            dataIndex:'name',
								                            //width: 0.25
								                        }
								                    ]
								                },
								                {
								                    xtype: 'compositefield',
								                    anchor: '100%',
								                    fieldLabel: 'Созданы',
								                    items: [
								                        {
								                            xtype: 'datefield',
								                            name: 'created_from',
								                            flex: 1,
								                            fieldLabel: 'Label'
								                        },
								                        {
								                            xtype: 'datefield',
								                            name: 'created_to',
								                            flex: 1,
								                            fieldLabel: 'Label'
								                        }
								                    ]
								                }
								            ]
								        
								        },
								       
								    ]
							}, {
					        	xtype:'container',
					        	autoHeight: true,
					        	items:{
					        		xtype:'button',
					        		text:'Искать',
					        		handler:function(){
					        			var f;
					        			f=this.findParentByType('tabpanel').items.items[0].items.items[0].getForm();
					        			//alert();
					        			var n,i;
					        			n = Ext.getCmp('nas_filter').getSelectedRecords();
					        			//alert(Ext.getCmp('nas_filter').getSelectedRecords()[0].data['value']);
					        			//alert(n.getSelectedRecords().len());
					        			for(i in n){
					        				//alert(i.data.value);
					        				//console.info(i);
					        				alert(i.constructor);
					        				
					        			}
					        			EBS.store.accounts.load({'params':f.getValues()})
					        		}
					        		}
					        }]},
					    	{
					      		xtype :'ebs_accountsPanel',
					    		id    :'ebs_accountsPanel'
					    	},
						
						]
						


        		}
           // apply config
           Ext.apply(this, Ext.apply(this.initialConfig, config));
    
           EBS.AccountsPanel.superclass.initComponent.apply(this, arguments);
       } // eo function initComponent
    
       ,onRender:function() {
           var me = this;
           
           EBS.AccountsPanel.superclass.onRender.apply(this, arguments);
       } // eo function onRender
     

   });
    Ext.reg('xaccountspanel', EBS.AccountsPanel);
    EBS.windows.keys[EBS.windows.keys.length] = 'xaccountspanel';
    
    EBS.TrTypeCombo = Ext.extend(Ext.form.ComboBox, {
        initComponent:function() {
           var config = {
        		    anchor: '100%',
        		    fieldLabel: 'Тип платежа',
        		    displayField: 'name',
        		    valueField: 'id', 
        		    mode: 'remote',
        		    editable:false,
        		    triggerAction: 'all',
        		    typeAhead: true,
        		    store:new Ext.data.Store({
        		    	autoLoad:true,
        		        proxy: new Ext.data.HttpProxy({
        		            url: '/ebsadmin/transactiontypes/',
        		            method:'GET',
        		            
        		        }),
        		        
        		        reader: new Ext.data.JsonReader({
        		            root: 'records'
        		        }, [{
        		            name: 'id'
        		        }, {
        		            name: 'name'
        		        }])
        		    }),

        		}
           // apply config
           Ext.apply(this, Ext.apply(this.initialConfig, config));
    
           EBS.TrTypeCombo.superclass.initComponent.apply(this, arguments);
       } // eo function initComponent
    
       ,onRender:function() {
           var me = this;
           this.store.on('load',function(store) {
             me.setValue('7', true);
           })
           EBS.TrTypeCombo.superclass.onRender.apply(this, arguments);
       } // eo function onRender
     

   });
    Ext.reg('xtrtypecombo', EBS.TrTypeCombo);
    
    EBS.gs=function gridStoreFactory() {
        return new Ext.data.JsonStore({
	        	paramsAsHash: true,
			    //	autoLoad: {params:{start:0, limit:100}},
   		        	proxy: new Ext.data.HttpProxy({
   		        		url: '/ebsadmin/subaccounts/',
   		        		method:'POST',
   		        	}),    
   		        	fields: ['switch_port', 'vpn_ipv6_ipinuse', 'ipn_speed', 'allow_dhcp', 'vpn_ip_address', 'allow_dhcp_with_block', 'ipn_sleep', 'speed', 'id', 'allow_addonservice', 'ipn_mac_address', 'allow_dhcp_with_minus', 'ipn_enabled', 'vpn_ipinuse', 'ipv4_vpn_pool', 'nas', 'ipv4_ipn_pool', 'allow_ipn_with_null', 'allow_ipn_with_minus', 'username', 'allow_dhcp_with_null', 'associate_pptp_ipn_ip', 'ipn_ip_address', 'associate_pppoe_ipn_mac', 'allow_ipn_with_block', 'vlan', 'allow_mac_update', 'allow_vpn_with_null', 'ipn_ipv6_ip_address', 'vpn_speed', 'allow_vpn_with_minus', 'password', 'ipn_added', 'account', 'ipn_ipinuse', 'switch', 'allow_vpn_with_block', 'need_resync', 'vpn_ipv6_ip_address'],
   		        	root: 'records',
   		        	remoteSort:true,
   		        	sortInfo:{
   		        		field:'username',
   		        		direction:'ASC'
   		        	},

        	   });
    }
    
    EBS.SubAccountsGrid = Ext.extend(Ext.grid.GridPanel, {
        initComponent:function() {
           var config = {
            	   xtype:'grid',
                   stateful: true,
                   stateId: 'stateSubaccountsGrid',
            	   store:new Ext.data.JsonStore({
       		        	paramsAsHash: true,
    			    //	autoLoad: {params:{start:0, limit:100}},
       		        	proxy: new Ext.data.HttpProxy({
       		        		url: '/ebsadmin/subaccounts/',
       		        		method:'POST',
       		        	}),    
       		        	fields: ['switch_port', 'vpn_ipv6_ipinuse', 'ipn_speed', 'allow_dhcp', 'vpn_ip_address', 'allow_dhcp_with_block', 'ipn_sleep', 'speed', 'id', 'allow_addonservice', 'ipn_mac_address', 'allow_dhcp_with_minus', 'ipn_enabled', 'vpn_ipinuse', 'ipv4_vpn_pool', 'nas', 'ipv4_ipn_pool', 'allow_ipn_with_null', 'allow_ipn_with_minus', 'username', 'allow_dhcp_with_null', 'associate_pptp_ipn_ip', 'ipn_ip_address', 'associate_pppoe_ipn_mac', 'allow_ipn_with_block', 'vlan', 'allow_mac_update', 'allow_vpn_with_null', 'ipn_ipv6_ip_address', 'vpn_speed', 'allow_vpn_with_minus', 'password', 'ipn_added', 'account', 'ipn_ipinuse', 'switch', 'allow_vpn_with_block', 'need_resync', 'vpn_ipv6_ip_address'],
       		        	root: 'records',
       		        	remoteSort:true,
       		        	sortInfo:{
       		        		field:'username',
       		        		direction:'ASC'
       		        	},

            	   }),
            	   bbar: new Ext.PagingToolbar({
                       pageSize: 100,
                      // store: this.store,
                       displayInfo: true,
                       dispalyMsg: i18n.paginatorDispalyMsg,
                       emptyMsg: i18n.paginatorEmptyMsg
                       //plugins: [new Ext.ux.SlidingPager(), this.filters],
                    }),
                selModel : new Ext.grid.RowSelectionModel({
                     singleSelect : true
                        }),
            	   //autoHeight: true,
            	   //autoWidth: true,
            	   listeners: {
 			          render:function(){
 			             // console.info('load',this,arguments);
 			        	  var account_id;
 			        	  account_id=this.findParentByType('tabpanel').items.items[0].getForm().findField('id').value;
 			        	  if (account_id){
 			        		  this.store.load({params:{account_id:account_id}});
 			        	  }
 			          }
            	   },
                   
            	   autoScroll: true,
            	   columns:[
            	            {
            	            	header:'id',
            	            	dataIndex:'id',
            	            	sortable:true
            	            },
            	            {
            	            	header:'Username',
            	            	dataIndex:'username',
            	            	sortable:true
            	            },
            	            {
            	            	header:'Сервер доступа',
            	            	dataIndex:'nas',
            	            	sortable:true
            	            },
            	            {
            	            	header:'IPv4 VPN',
            	            	dataIndex:'vpn_ip_address',
            	            	sortable:true
            	            },
            	            {
            	            	header:'IPv4 IPN',
            	            	dataIndex:'ipn_ip_address',
            	            	sortable:true
            	            },
            	            {
            	            	header:'MAC',
            	            	dataIndex:'ipn_mac_address',
            	            	sortable:true
            	            },
            	            {
            	            	header:'Коммутатор',
            	            	dataIndex:'switch',
            	            	sortable:true
            	            },
            	            {
            	            	header:'Порт коммутатора',
            	            	dataIndex:'switch_port',
            	            	sortable:true
            	            },
            	            {
            	            	header:'Custom VPN speed',
            	            	dataIndex:'vpn_speed',
            	            	sortable:true
            	            },
            	            {
            	            	header:'Custom IPN speed',
            	            	dataIndex:'ipn_speed',
            	            	sortable:true
            	            },
            	            {
            	            	header:'Не выполнять IPN действия',
            	            	dataIndex:'ipn_sleep',
            	            	sortable:true
            	            },                                                           	            
            	            {
            	            	header:'IPN добавлен',
            	            	dataIndex:'ipn_added',
            	            	sortable:true
            	            },  
            	            {
            	            	header:'IPN активен',
            	            	dataIndex:'ipn_enabled',
            	            	sortable:true
            	            },                                                          	            
            	            ]
            		   
            		  
               }

        		
           // apply config
           Ext.applyIf(this, Ext.apply(this.initialConfig, config));
    
           EBS.SubAccountsGrid.superclass.initComponent.apply(this, arguments);
       } // eo function initComponent
    


   });

   Ext.reg('xsubaccountsgrid', EBS.SubAccountsGrid);
   
   EBS.AccountAddonServiceGrid = Ext.extend(Ext.grid.GridPanel, {
       initComponent:function() {
          var config = {
           	   xtype:'grid',
                  stateful: true,
                  stateId: 'stateAccountAddonServiceGrid',
           	   	  store:new Ext.data.JsonStore({
      		        	paramsAsHash: true,

      		        	autoLoad: {params:{start:0, limit:100,'subaccount_id': this.findParentByType('form').findParentByType('panel').instance_id}},
      		        	proxy: new Ext.data.HttpProxy({
      		        		url: '/ebsadmin/accountaddonservices/',
      		        		method:'POST',
      		        	}),    
      		        	fields: [{name: 'service', type:'int'},
      		        		{name: 'account', type:'int'},
      		        		{name: 'id', type:'int'},
      		        		{name: 'subaccount', type:'int'},
      		        		{name: 'activated', type: 'date', dateFormat: Date.patterns.ISO8601Long},
      		        		{name: 'deactivated',  type: 'date', dateFormat: Date.patterns.ISO8601Long},
      		        		{name: 'action_status', type:'boolean'},
      		        		{name: 'speed_status', type:'boolean'},
      		        		{name: 'temporary_blocked', type: 'date', dateFormat: Date.patterns.ISO8601Long},
      		        		{name: 'last_checkout', type: 'date', dateFormat: Date.patterns.ISO8601Long},],
      		        	root: 'records',
      		        	remoteSort:true,
      		        	sortInfo:{
      		        		field:'username',
      		        		direction:'ASC'
      		        	},



           	   }),

               selModel : new Ext.grid.RowSelectionModel({
                    singleSelect : true
                       }),
           	   //autoHeight: true,
           	   //autoWidth: true,
           	   listeners: {
			          render:function(){
			             // console.info('load',this,arguments);
			        	  //alert(this.findParentByType('form').findParentByType('panel').instance_id);
			        	  //this.store.setBaseParam('subaccount_id', this.findParentByType('form').findParentByType('panel').instance_id);
			        	  //this.store.load();
			          }
           	   },
                  
           	   autoScroll: true,
           	   columns:[
           	            {
           	            	header:'id',
           	            	dataIndex:'id',
           	            	sortable:true
           	            },
           	            {
           	            	header:'Услуга',
           	            	dataIndex:'service',
           	            	sortable:true
           	            },
           	            {
           	            	header:'Активирована',
           	            	dataIndex:'activated',
           	            	sortable:true,
           	            	renderer:Ext.util.Format.dateRenderer(Date.patterns.ISO8601Long),
           	            	
           	            },
           	            {
           	            	header:'Отключена',
           	            	dataIndex:'deactivated',
           	            	sortable:true,
           	            	renderer:Ext.util.Format.dateRenderer(Date.patterns.ISO8601Long),
           	            },
           	            {
           	            	header:'Последнее списание',
           	            	dataIndex:'last_checkout',
           	            	sortable:true,
           	            	renderer:Ext.util.Format.dateRenderer(Date.patterns.ISO8601Long),
           	            },
           	            {
           	            	header:'Команда активации выполнена',
           	            	dataIndex:'action_status',
           	            	sortable:true
           	            },
           	            {
           	            	header:'Команда установки скорости выполнена',
           	            	dataIndex:'speed_status',
           	            	sortable:true
           	            },
           	            ]
           		   
           		  
              }

       		
          // apply config
          Ext.applyIf(this, Ext.apply(this.initialConfig, config));
   
          EBS.AccountAddonServiceGrid.superclass.initComponent.apply(this, arguments);
      } // eo function initComponent
   


  });

  Ext.reg('xaccountaddonservicesgrid', EBS.AccountAddonServiceGrid);
  
   EBS.ComboCity = Ext.extend(Ext.form.ComboBox, {
       initComponent:function() {
          var config = {
       		    anchor: '100%',
       		    fieldLabel: 'Город',
       		    displayField: 'name',
       		    valueField: 'id', 
       		    mode: 'remote',
       		    editable:false,
       		    triggerAction: 'all',
       		    typeAhead: true,
       		    store:new Ext.data.Store({
       		    	autoLoad:true,
       		        proxy: new Ext.data.HttpProxy({
       		            url: '/ebsadmin/city/',
       		            method:'GET',
       		            
       		        }),
       		        
       		        reader: new Ext.data.JsonReader({
       		            root: 'records'
       		        }, [{
       		            name: 'id'
       		        }, {
       		            name: 'name'
       		        }])
       		    }),

       		}
          // apply config
          Ext.apply(this, Ext.apply(this.initialConfig, config));
   
          EBS.ComboCity.superclass.initComponent.apply(this, arguments);
      } // eo function initComponent
   
      ,onRender:function() {
          var me = this;
          this.store.on('load',function(store) {
            me.setValue(null, true);
          })
          EBS.ComboCity.superclass.onRender.apply(this, arguments);
      } // eo function onRender
    

  });
   
  Ext.reg('xcombocity', EBS.ComboCity);
  
  EBS.ComboAddedLocal = Ext.extend(Ext.form.ComboBox, {
      initComponent:function() {
         var config = {
      		    anchor: '100%',
      		    editable:false,
      		    store: new Ext.data.ArrayStore({
                    fields: ['name', 'value'],
                    data : [['Добавлен',true],['Не добавлен',false],] // from states.js
                }),
                valueField:'value',
                displayField:'name',
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                

      		}
         // apply config
         Ext.apply(this, Ext.applyIf(this.initialConfig, config));
  
         EBS.ComboAddedLocal.superclass.initComponent.apply(this, arguments);
     } // eo function initComponent
  
     ,onRender:function() {
         var me = this;
         this.store.on('load',function(store) {
           //me.setValue('7', true);
         })
         EBS.ComboAddedLocal.superclass.onRender.apply(this, arguments);
     } // eo function onRender
   

 });
  
 Ext.reg('xcomboaddedlocal', EBS.ComboAddedLocal);

 EBS.ComboEnabledLocal = Ext.extend(Ext.form.ComboBox, {
     initComponent:function() {
        var config = {
     		    anchor: '100%',
     		    editable:false,
     		    store: new Ext.data.ArrayStore({
                   fields: ['name', 'value'],
                   data : [['Активирован',true],['Не активирован',false],] // from states.js
               }),
               valueField:'value',
               displayField:'name',
               typeAhead: true,
               mode: 'local',
               triggerAction: 'all',
               

     		}
        // apply config
        Ext.apply(this, Ext.applyIf(this.initialConfig, config));
 
        EBS.ComboAddedLocal.superclass.initComponent.apply(this, arguments);
    } // eo function initComponent
 
    ,onRender:function() {
        var me = this;
        this.store.on('load',function(store) {
          //me.setValue('7', true);
        })
        EBS.ComboEnabledLocal.superclass.onRender.apply(this, arguments);
    } // eo function onRender
  

});
 
Ext.reg('xcomboenabledlocal', EBS.ComboEnabledLocal);

  EBS.ComboStreet = Ext.extend(Ext.form.ComboBox, {
      initComponent:function() {
         var config = {
      		    anchor: '100%',
      		    fieldLabel: 'Улица',
      		    displayField: 'name',
      		    valueField: 'id', 
      		    mode: 'remote',
      		    //editable:true,
                loadingText  : 'Searching...',
                pageSize     : 5,
      		    triggerAction: 'all',
      		    typeAhead: true,
      		    store:new Ext.data.Store({
      		    	autoLoad:true,
      		        proxy: new Ext.data.HttpProxy({
      		            url: '/ebsadmin/street/',
      		            method:'GET',
      		            
      		        }),
      		        
      		        reader: new Ext.data.JsonReader({
      		            root: 'records'
      		        }, [{
      		            name: 'id'
      		        }, {
      		            name: 'name'
      		        }])
      		    }),

      		}
         // apply config
         Ext.apply(this, Ext.apply(this.initialConfig, config));
  
         EBS.ComboStreet.superclass.initComponent.apply(this, arguments);
     } // eo function initComponent
  
     ,onRender:function() {
         var me = this;
         this.store.on('load',function(store) {
           me.setValue(null, true);
         })
         EBS.ComboStreet.superclass.onRender.apply(this, arguments);
     } // eo function onRender
   

 });
  
 Ext.reg('xcombostreet', EBS.ComboStreet);
   
 EBS.ComboHouse = Ext.extend(Ext.form.ComboBox, {
     initComponent:function() {
        var config = {
     		    anchor: '100%',
     		    fieldLabel: 'Дом',
     		    displayField: 'name',
     		    valueField: 'id', 
     		    mode: 'remote',
     		    editable:false,
     		    triggerAction: 'all',
     		    typeAhead: true,
     		    store:new Ext.data.Store({
     		    	//autoLoad:true,
     		        proxy: new Ext.data.HttpProxy({
     		            url: '/ebsadmin/house/',
     		            method:'GET',
     		            
     		        }),
     		        
     		        reader: new Ext.data.JsonReader({
     		            root: 'records'
     		        }, [{
     		            name: 'id'
     		        }, {
     		            name: 'name'
     		        }])
     		    }),

     		}
        // apply config
        Ext.apply(this, Ext.apply(this.initialConfig, config));
 
        EBS.ComboHouse.superclass.initComponent.apply(this, arguments);
    } // eo function initComponent
 
    ,onRender:function() {
        var me = this;
        this.store.on('load',function(store) {
        	if (!this.value){
          //me.setValue(null, true);
        	};
        })
        this.store.load();
        EBS.ComboHouse.superclass.onRender.apply(this, arguments);
    } // eo function onRender
  

});
 
Ext.reg('xcombohouse', EBS.ComboHouse);

EBS.SystemUser = Ext.extend(Ext.form.ComboBox, {
    initComponent:function() {
       var config = {
    		    anchor: '100%',
    		    displayField: 'name',
    		    valueField: 'id', 
    		    mode: 'remote',
    		    editable:false,
    		    triggerAction: 'all',
    		    typeAhead: true,
    		    store:new Ext.data.Store({
    		    	autoLoad:true,
    		        proxy: new Ext.data.HttpProxy({
    		            url: '/ebsadmin/systemuser/',
    		            method:'GET',
    		            
    		        }),
    		        
    		        reader: new Ext.data.JsonReader({
    		            root: 'records'
    		        }, [{
    		            name: 'id'
    		        }, {
    		            name: 'name'
    		        }])
    		    }),

    		}
       // apply config
       Ext.apply(this, Ext.apply(this.initialConfig, config));

       EBS.SystemUser.superclass.initComponent.apply(this, arguments);
   } // eo function initComponent

   ,onRender:function() {
       var me = this;
       this.store.on('load',function(store) {
         me.setValue(null, true);
       })
       EBS.SystemUser.superclass.onRender.apply(this, arguments);
   } // eo function onRender
 

});

Ext.reg('xcombosystemuser', EBS.SystemUser);

EBS.ComboAccountStatus = Ext.extend(Ext.form.ComboBox, {
    initComponent:function() {
       var config = {
    		    anchor: '100%',
    		    displayField: 'name',
    		    valueField: 'id', 
    		    mode: 'remote',
    		    editable:false,
    		    triggerAction: 'all',
    		    typeAhead: true,
    		    store:new Ext.data.Store({
    		    	autoLoad:true,
    		        proxy: new Ext.data.HttpProxy({
    		            url: '/ebsadmin/accountstatus/',
    		            method:'GET',
    		            
    		        }),
    		        
    		        reader: new Ext.data.JsonReader({
    		            root: 'records'
    		        }, [{
    		            name: 'id'
    		        }, {
    		            name: 'name'
    		        }])
    		    }),

    		}
       // apply config
       Ext.apply(this, Ext.applyIf(this.initialConfig, config));

       EBS.ComboAccountStatus.superclass.initComponent.apply(this, arguments);
   } // eo function initComponent

   ,onRender:function() {
       var me = this;
       this.store.on('load',function(store) {
         me.setValue(1, true);
       })
       EBS.ComboAccountStatus.superclass.onRender.apply(this, arguments);
   } // eo function onRender
 

});

Ext.reg('xcomboaccountstatus', EBS.ComboAccountStatus);

EBS.ComboNas = Ext.extend(Ext.form.ComboBox, {
    initComponent:function() {
       var config = {
    		    anchor: '100%',
    		    displayField: 'name',
    		    valueField: 'id', 
    		    mode: 'remote',
    		    editable:false,
    		    triggerAction: 'all',
    		    typeAhead: true,
    		    store:new Ext.data.Store({
    		    	autoLoad:true,
    		        proxy: new Ext.data.HttpProxy({
    		            url: '/ebsadmin/nas/',
    		            method:'GET',
    		            
    		        }),
    		        
    		        reader: new Ext.data.JsonReader({
    		            root: 'records'
    		        }, [{
    		            name: 'id'
    		        }, {
    		            name: 'name'
    		        }])
    		    }),

    		}
       // apply config
       Ext.apply(this, Ext.apply(this.initialConfig, config));

       EBS.ComboNas.superclass.initComponent.apply(this, arguments);
   } // eo function initComponent

   ,onRender:function() {
       var me = this;
       this.store.on('load',function(store) {
         me.setValue(null, true);
       })
       EBS.ComboNas.superclass.onRender.apply(this, arguments);
   } // eo function onRender
 

});

Ext.reg('xcombonas', EBS.ComboNas);
 

EBS.ComboIpPool = Ext.extend(Ext.form.ComboBox, {
    initComponent:function() {
       var config = {
    		    anchor: '100%',
    		    displayField: 'name',
    		    valueField: 'id', 
    		    mode: 'remote',
    		    editable:false,
    		    triggerAction: 'all',
    		    pool_type:0,
    		    typeAhead: true,
    		    store:new Ext.data.Store({
    		    	autoLoad:true,
    		        proxy: new Ext.data.HttpProxy({
    		            url: '/ebsadmin/ippool/',
    		            method:'POST',
    		            
    		        }),
    		        
    		        reader: new Ext.data.JsonReader({
    		            root: 'records'
    		        }, [{
    		            name: 'id'
    		        }, {
    		            name: 'name'
    		        }])
    		    }),

    		}
       // apply config
       
       Ext.apply(this, Ext.applyIf(this.initialConfig, config));
       
       EBS.ComboIpPool.superclass.initComponent.apply(this, arguments);
       this.store.setBaseParam('pool_type', this.pool_type);
   } // eo function initComponent

   ,onRender:function() {
       var me = this;
       this.store.setBaseParam('pool_type', this.pool_type);
       //this.store.load({params:{'pool_type':this.pool_type}})
       EBS.ComboIpPool.superclass.onRender.apply(this, arguments);
   } // eo function onRender
 

});

Ext.reg('xcomboippool', EBS.ComboIpPool);

EBS.ComboSwitch = Ext.extend(Ext.form.ComboBox, {
    initComponent:function() {
       var config = {
    		    anchor: '100%',
    		    displayField: 'name',
    		    valueField: 'id', 
    		    mode: 'remote',
    		    editable:false,
    		    triggerAction: 'all',
    		    typeAhead: true,
    		    store:new Ext.data.Store({
    		    	autoLoad:true,
    		        proxy: new Ext.data.HttpProxy({
    		            url: '/ebsadmin/switch/',
    		            method:'GET',
    		            
    		        }),
    		        
    		        reader: new Ext.data.JsonReader({
    		            root: 'records'
    		        }, [{
    		            name: 'id'
    		        }, {
    		            name: 'name'
    		        }])
    		    }),

    		}
       // apply config
       Ext.apply(this, Ext.apply(this.initialConfig, config));

       EBS.ComboSwitch.superclass.initComponent.apply(this, arguments);
       //this.store.setBaseParam('pool_type', this.pool_type);
   } // eo function initComponent

   ,onRender:function() {
       var me = this;
       this.store.on('load',function(store) {
         me.setValue(null, true);
       })
       EBS.ComboSwitch.superclass.onRender.apply(this, arguments);
   } // eo function onRender
 

});

Ext.reg('xcomboswitch', EBS.ComboSwitch);
/* EOF BASE Components*/





















});













/*
 


   this.topToolbar = [
                         {
                            //text: 'ok',
                            icon: media+'icons/16/new/wand.png',
                            height:32,
                            width:32,
                            tooltip: 'Just a magic!',
                            handler: function () {}
                        },
                         {
                            text: 'Print',
                            icon: media+'icons/16/new/printer.png',
                            height:32,
                            width:32,
                            tooltip: 'Print current panel',
                            handler: function () {
                                //Ext.ux.Printer.print(mainPanel)
                            }
                        },
                        {
                            xtype: 'tbfill'
                        },
                        {
                            xtype: 'tbbutton',
                            id:'exclamation',
                            text: '<b>10</b> New messages',
                            tooltip: 'Urgent messages from administration',
                            icon: media+'/helpdesk_img/show_comments.png'
                        },
                        {
                            xtype: 'tbseparator'
                        },
                        {
                            xtype: 'tbbutton',
                            text: 'Username',
                            icon: media+'icons/16/new/user.png',
                            height:32,
                            width:32,
                            menu: [{
                                text: 'Settings',
                                icon: media+'icons/16/new/cog.png'
                            },
                            {
                                text: 'Item'
                            },
                            {
                                xtype: 'tbseparator'
                            },
                            {
                                text: 'Logout',
                                icon: media+'icons/16/new/door_out.png'
                            }]
                        }

                    ];


 */















/*
 *tests:
Создаст все доступные окна

for(i=0;i<EBS.windows.keys.length;i++){
    cmp =Ext.create({xtype:EBS.windows.keys[i]});
    Ext.getCmp('main_tab_panel').add(cmp);
}

 */
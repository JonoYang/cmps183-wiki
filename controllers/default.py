# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

import logging


def index():

    title = request.args(0) or 'Main'
    title = title.lower()
    display_title = title.title()

    if db(db.pagetable.title == title).select().first() is None:
        redirect(URL('default', 'new', args=[title]))

    page_id = db(db.pagetable.title == title).select().first().id

    rev = db(db.revision.pagetable_id == page_id).select(orderby=~db.revision.date_created).first()
    s = rev.body

    editing = request.vars.edit == 'y'

    if editing:
        form = SQLFORM.factory(Field('body', 'text',
                                     label='Content',
                                     default=s
                                     ))
        form.add_button('History', URL('default', 'history', args=[title]))
        form.add_button('Cancel', URL('default', 'index', args=[title]))

        if form.process().accepted:
            db.revision.insert(author = auth.user_id, body=form.vars.body, pagetable_id = page_id)
            redirect(URL('default', 'index', args=[title]))

        content = form
    else:
        content = s

    button = A('edit', _class='btn', _href=URL('default', 'index', args=[title], vars=dict(edit='y')))

    return dict(display_title = display_title,
                button  = button,
                content = content,
                editing = editing
                )

def new():
    title = request.args(0)
    content = 'Would you like to create the page for %s?' % (title)
    create_button = A('Create page', _class='btn', _href=URL('default', 'create', args=[title]))
    cancel_button = A('Cancel', _class='btn', _href=URL('default', 'index'))
    return dict(content = content,
                create_button = create_button,
                cancel_button = cancel_button,
                title = title
                )

def create():
    title = request.args(0)
    form = SQLFORM.factory(Field('body', 'text',
                                  label='Content'
                                ))
    form.add_button('Cancel', URL('default', 'index'))
    if form.process().accepted:
        db.pagetable.insert(title=title)
        page_id = db(db.pagetable.title == title).select().first().id 
        db.revision.insert(author = auth.user_id, body=form.vars.body, pagetable_id = page_id)
        redirect(URL('default', 'index', args=[title]))
    return dict(form = form, title = title)

def history():
    title = request.args(0)
    page_id = db(db.pagetable.title == title).select().first().id
    rev = db(db.revision.pagetable_id == page_id).select(orderby=~db.revision.date_created)

    revising = request.vars.rev == 'y'

    if revising:
        rev_id = request.args(1)
        rev = db(db.revision.id == rev_id).select().first()
        db.revision.insert(author = auth.user_id, body=rev.body, pagetable_id = page_id)
        redirect(URL('default', 'index', args=[title]))

    return dict(title = title, rev = rev)

def revision():
    title = request.args(0)
    rev_id = request.args(1)
    page_id = db(db.pagetable.title == title).select().first().id
    rev = db(db.revision.id == rev_id).select().first()
    s = rev.body

    form = SQLFORM.factory(Field('body', 'text',
                                label='Content',
                                default=s
                                ))
    form.add_button('History', URL('default', 'history', args=[title]))
    form.add_button('Cancel', URL('default', 'index', args=[title]))

    if form.process().accepted:
        db.revision.insert(author = auth.user_id, body=form.vars.body, pagetable_id = page_id)
        redirect(URL('default', 'index', args=[title]))

    return dict(title = title, form = form)

def test():
    """This controller is here for testing purposes only.
    Feel free to leave it in, but don't make it part of your wiki.
    """
    title = "This is the wiki's test page"
    form = None
    content = None
    
    # Let's uppernice the title.  The last 'title()' below
    # is actually a Python function, if you are wondering.
    display_title = title.title()
    
    # Gets the body s of the page.
    r = db.testpage(1)
    s = r.body if r is not None else ''
    # Are we editing?
    editing = request.vars.edit == 'true'
    # This is how you can use logging, very useful.
    logger.info("This is a request for page %r, with editing %r" %
                 (title, editing))
    if editing:
        # We are editing.  Gets the body s of the page.
        # Creates a form to edit the content s, with s as default.
        form = SQLFORM.factory(Field('body', 'text',
                                     label='Content',
                                     default=s
                                     ))
        # You can easily add extra buttons to forms.
        form.add_button('Cancel', URL('default', 'test'))
        # Processes the form.
        if form.process().accepted:
            # Writes the new content.
            if r is None:
                # First time: we need to insert it.
                db.testpage.insert(id=1, body=form.vars.body)
            else:
                # We update it.
                r.update_record(body=form.vars.body)
            # We redirect here, so we get this page with GET rather than POST,
            # and we go out of edit mode.
            redirect(URL('default', 'test'))
        content = form
    else:
        # We are just displaying the page
        content = s
    return dict(display_title=display_title, content=content, editing=editing)


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login() 
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)

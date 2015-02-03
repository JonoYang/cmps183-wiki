# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

import logging


def index():
    """
    This is the main page of the wiki.  
    You will find the title of the requested page in request.args(0).
    If this is None, then just serve the latest revision of something titled "Main page" or something 
    like that. 
    """
    title = request.args(0) or 'main page'

    # Let's uppernice the title.  The last 'title()' below
    # is actually a Python function, if you are wondering.
    display_title = title.title()

    # You have to serve to the user the most recent revision of the 
    # page with title equal to title.
    page_id = db(db.pagetable.title == title).select().first()

    rev = db(db.revision.ref_id == page_id).select(orderby=~db.revision.date_created).first()

    s = rev.body if rev is not None else ''

    editing = request.vars.edit == 'y'

    if editing:
        # We are editing.  Gets the body s of the page.
        # Creates a form to edit the content s, with s as default.
        form = SQLFORM.factory(Field('body', 'text',
                                     label='Content',
                                     default=s
                                     ))
        # You can easily add extra buttons to forms.
        form.add_button('Cancel', URL('default', 'index', args=[title]))
        # Processes the form.
        if form.process().accepted:
            # Writes the new content.
            if rev is None:
                # First time: we need to insert it.
                db.pagetable.insert(id=1, title=title)
                db.revision.insert(id=1, body=form.vars.body)
            else:
                # We update it.
                rev.update_record(body=form.vars.body)
            # We redirect here, so we get this page with GET rather than POST,
            # and we go out of edit mode.
            redirect(URL('default', 'index'))
        content = form
    else:
        # We are just displaying the page
        content = s

    # Here, I am faking it.  
    # Produce the content from real database data. 
    button = A('edit', _class='btn', _href=URL('default', 'index', args=[title], vars=dict(edit='y')))
    #content_w = represent_wiki(content)
    return dict(display_title = display_title,
                button = button,
                content = content,
                editing=editing
                )


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

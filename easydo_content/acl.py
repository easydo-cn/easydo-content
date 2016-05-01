# -*- encoding: utf-8 -*-
from zope.component import getAdapter
from zope.security.management import checkPermission
from zope.securitypolicy.zopepolicy import globalRolesForPrincipal
from zope.securitypolicy.interfaces import IPrincipalRoleManager, IPrincipalRoleMap
from zope.securitypolicy.interfaces import IRolePermissionManager

from zope.securitypolicy.principalrole import principalRoleManager
globalPrincipalsForRole = principalRoleManager.getPrincipalsForRole

ROLE_MAP = {
'Manager':'zopen.Manager',
'Auditor':'zopen.Auditor',
'Reviewer':'zopen.Reviewer',
'Editor':'zopen.Editor',
'Owner':'zopen.Owner',
'Creator':'zopen.Creator',
'ContainerCreator':'zopen.ContainerCreator',
'Collaborator':'zopen.Collaborator',
'Responsible':'zopen.Responsible',
'Delegator':'zopen.Delegator',
'Subscriber':'zopen.Subscriber',
'Accessor':'zopen.Accessor',
'PrivateReader1':'zopen.PrivateReader1',
'PrivateReader2':'zopen.PrivateReader2',
'PrivateReader3':'zopen.PrivateReader3',
'PrivateReader4':'zopen.PrivateReader4',
'PrivateReader':'zopen.PrivateReader',
'Reader1':'zopen.Reader1',
'Reader2':'zopen.Reader2',
'Reader3':'zopen.Reader3',
'Reader4':'zopen.Reader4',
'Reader':'zopen.Reader',
}

ROLE_MAP2 = {}
for k,v in ROLE_MAP.items(): ROLE_MAP2[v] = k

PERM_MAP = {
'Public':'zope.Public',
'Manage':'zope.ManageContent',
'Review':'zopen.Review',
'Audit':'zopen.Audit',
'View':'zope.View',
"Comment":"zopen.Comment",
'Preview':'zopen.Preview',
'Print':'zopen.Print',
'Pdf':'zopen.Pdf',
'Operate':'zopen.Operate',
'Download':'zopen.Download',
'Access':'zopen.Access',
'Edit':'zopen.Edit',
'Add':'zopen.Add',
'Delegate':'zopen.Delegate',
'AddFolder':'zopen.AddFolder',
'AddContainer':'zopen.AddContainer',
'AddRevision':"zopen.AddRevision",
'SaveRevision':"zopen.SaveRevision",
'ManageRevision':"zopen.ManageRevision",
'ManagePublinshedRevision':"zopen.ManagePublishedRevision",
'Logined':'zopen.Logined',
}

PERM_MAP2 = {}
for k,v in PERM_MAP.items(): PERM_MAP2[v] = k

class ACL:

    def __init__(self, context):
        self.context = context

    def grant_role(self, role_id, pids):
        if isinstance(pids, basestring): pids = [pids]
        role_id = ROLE_MAP[role_id]
        prinrole = IPrincipalRoleManager(self.context)
        for pid in pids:
            prinrole.assignRoleToPrincipal(role_id, pid)

    def deny_role(self, role_id, pids):
        if isinstance(pids, basestring): pids = [pids]
        role_id = ROLE_MAP[role_id]
        prinrole = IPrincipalRoleManager(self.context)
        for pid in pids:
            prinrole.removeRoleFromPrincipal(role_id, pid)

    def unset_role(self, role_id, pids):
        if isinstance(pids, basestring): pids = [pids]
        role_id = ROLE_MAP[role_id]
        prinrole = IPrincipalRoleManager(self.context)
        for pid in pids:
           prinrole.unsetRoleForPrincipal(role_id, pid)

    def role_principals(self, role_id):
        role_id = ROLE_MAP[role_id]
        prinrole = getAdapter(self.context, IPrincipalRoleMap)
        return prinrole.getPrincipalsForRole(role_id)

    def inherited_role_principals(self, role_id):
        _role_id = ROLE_MAP[role_id]

        principals = {}

        for principal, setting in self.role_principals(role_id):
            if principal not in principals:
                principals[principal] = setting

        parent = getattr(self.context, '__parent__', None)
        if parent is None:
            for principal, setting in globalPrincipalsForRole(_role_id):
                if principal == 'zope.manager':
                    continue
                if principal not in principals:
                    principals[principal] = setting
        else:
            for principal, setting in ACL(parent).inherited_role_principals(role_id):
                if principal not in principals:
                    principals[principal] = setting

        return principals.items()

    def principal_roles(self, pid):
        prinrole = getAdapter(self.context, IPrincipalRoleMap)
        roles = prinrole.getRolesForPrincipal(pid)
        return [ROLE_MAP2[role] for role in roles]

    def inherited_principal_roles(self, pid):
        roles = {}

        for role,setting in self.principal_roles(pid):
            if role not in roles:
                roles[role] = setting

        parent = getattr(self.context, '__parent__', None)
        if parent is None:
            for role, setting in globalRolesForPrincipal(pid):
                if role not in roles:
                    roles[role] = setting
        else:
            for role, setting in ACL(parent).inherited_principal_roles(pid):
                if role not in roles:
                    roles[role] = setting

        roles = roles.items()
        return [ROLE_MAP2[role] for role in roles]

    def check_permission(self, permission_id):
        permission_id = PERM_MAP[permission_id]
        return checkPermission(permission_id, self.context)

    def grant_role_permission(self, role, permission):
        permission = PERM_MAP[permission]
        role = ROLE_MAP[role]
        IRolePermissionManager(self.context).grantPermissionToRole(permission, role)

    def deny_role_permission(self, role, permission):
        permission = PERM_MAP[permission]
        role = ROLE_MAP[role]
        IRolePermissionManager(self.context).denyPermissionToRole(permission, role)

    def unset_role_permission(self, role, permission):
        permission = PERM_MAP[permission]
        role = ROLE_MAP[role]
        IRolePermissionManager(self.context).unsetPermissionFromRole(permission, role)

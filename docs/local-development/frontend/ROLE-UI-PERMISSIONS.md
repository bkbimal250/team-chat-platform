# Role UI permissions

Capabilities derive from actual Organization role assignments for the Identity-validated member and tenant. OWNER is not platform authority. Multiple OWNER memberships use the same capabilities. Standard ADMIN lacks role.manage; MEMBER has organization/member/team/branch/role view and no management mutations. Navigation and data requests are permission gated, direct denied routes show an intentional alert; the backend enforces all requests.

Members filters use actual status/branch/team/role contracts. Update, remove, invitation create/revoke, branch/team assignment and ownership delegation remain backend protected. The frontend does not select one permanent organization owner.

Live local verification used Owner A, Owner B, Admin and Member identities created via registration/invitation acceptance. Second owner branch creation succeeded, member branch mutation returned 403, other-tenant branch read/update returned 404, two actual owner memberships were present. Test mocks are confined to tests; these live results did not rely on frontend role overrides.

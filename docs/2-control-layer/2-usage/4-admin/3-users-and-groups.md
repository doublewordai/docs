# Managing Users & Groups

Control Layer uses group-based access control to manage model permissions efficiently. This system allows you to control access for many users without individual permission management.

## Access Control Model

The relationship is straightforward: Users belong to groups, and groups have access to models. Users automatically inherit access to all models assigned to their groups.

This design simplifies permission management:

- Add a user to a group to grant model access
- Remove a user from a group to revoke access
- Assign new models to existing groups to expand access
- Create new groups for specialized access patterns

Changes take effect immediately. Users see updated model lists as soon as their group membership changes.

![Control Layer Users & Groups Interface](/img/control-layer-users-groups.png)
*The Users & Groups interface - manage user access and group permissions from one place*

## User Management

Users are created automatically when they first sign in through your authentication provider. Control Layer uses the email address from the authentication system as the user identifier.

The initial admin user specified in configuration has permanent administrative privileges. This ensures at least one administrator always exists. Grant administrative privileges to other users as needed, but do so judiciously – administrators have full system control.

Regular users can only access models through group membership. They cannot modify system configuration, manage other users, or change model sources.

## Group Strategy

Design your group structure to minimize ongoing maintenance. Consider these
common patterns:

**Department-based groups**: Create groups for engineering, data science,
marketing, etc. Assign models relevant to each department's work.

**Project-based groups**: Establish groups for specific projects or
initiatives. This allows temporary access that's easy to revoke when projects
complete.

**Access-level groups**: Set up groups like "basic-models", "advanced-models",
or "expensive-models" to control access based on cost or capability.

**Default access group**: Create an "all-users" group for models everyone
should access. Add all users to this group for baseline access.

## Managing Group Membership

Add users to groups based on their roles and requirements. Users can belong to
multiple groups, inheriting access from all of them.

Review group memberships periodically. Remove users who no longer need access,
especially contractors or users who've changed roles. This practice maintains
security and potentially reduces costs.

When users report access issues, check their group memberships first. Ensure
they belong to groups with the required models assigned.

## Special Considerations

**External Users**: Create separate groups for contractors or partners. This
makes it easy to revoke access when relationships end.

**Testing Groups**: Establish groups for testing new models or experimental
features. Limit membership to prevent accidental high costs.

**Compliance Requirements**: If certain models process sensitive data, create
restricted groups with documented membership policies.

## Troubleshooting Access

**User can't see expected models**: Verify group membership and that models are
assigned to those groups. Check that models are currently available.

**User has unexpected access**: Review all group memberships. Users might
belong to groups you didn't expect.

**Bulk access changes needed**: Plan group structure changes carefully.
Consider creating new groups and migrating users rather than modifying existing
groups.

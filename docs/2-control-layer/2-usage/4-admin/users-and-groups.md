# Users and Groups

Control Layer uses group-based access control to manage model permissions efficiently. This system allows you to control access for many users without individual permission management.

## Access Control Model

The relationship is straightforward: Users belong to groups, and groups have access to models. Users automatically inherit access to all models assigned to their groups.

This design simplifies permission management:
- Add a user to a group to grant model access
- Remove a user from a group to revoke access
- Assign new models to existing groups to expand access
- Create new groups for specialized access patterns

Changes take effect immediately. Users see updated model lists as soon as their group membership changes.

## User Management

Users are created automatically when they first sign in through your authentication provider. Control Layer uses the email address from the authentication system as the user identifier.

The initial admin user specified in configuration has permanent administrative privileges. This ensures at least one administrator always exists. Grant administrative privileges to other users as needed, but do so judiciously – administrators have full system control.

Regular users can only access models through group membership. They cannot modify system configuration, manage other users, or change model sources.

## Group Strategy

Design your group structure to minimize ongoing maintenance. Consider these common patterns:

**Department-based groups**: Create groups for engineering, data science, marketing, etc. Assign models relevant to each department's work.

**Project-based groups**: Establish groups for specific projects or initiatives. This allows temporary access that's easy to revoke when projects complete.

**Access-level groups**: Set up groups like "basic-models", "advanced-models", or "expensive-models" to control access based on cost or capability.

**Default access group**: Create an "all-users" group for models everyone should access. Add all users to this group for baseline access.

## Managing Group Membership

Add users to groups based on their roles and requirements. Users can belong to multiple groups, inheriting access from all of them.

Review group memberships periodically. Remove users who no longer need access, especially contractors or users who've changed roles. This practice maintains security and potentially reduces costs.

When users report access issues, check their group memberships first. Ensure they belong to groups with the required models assigned.

## Model Assignment

Assign models to groups based on the group's purpose. Each group can have multiple models, and models can belong to multiple groups.

Consider model costs when making assignments. Expensive models should typically be assigned to smaller, specialized groups rather than broad access groups.

Monitor model usage by group to understand consumption patterns. This data helps optimize group structures and identify potential cost savings.

## Special Considerations

**External Users**: Create separate groups for contractors or partners. This makes it easy to revoke access when relationships end.

**Testing Groups**: Establish groups for testing new models or experimental features. Limit membership to prevent accidental high costs.

**Compliance Requirements**: If certain models process sensitive data, create restricted groups with documented membership policies.

## Access Patterns

Common access patterns and their implementation:

**Everyone gets basic models**: Create an all-users group with GPT-3.5, Claude Instant, or similar cost-effective models.

**Specialists get advanced models**: Create role-specific groups with access to GPT-4, Claude Opus, or specialized models.

**Temporary project access**: Create project groups that can be deleted when projects complete, automatically revoking access.

**Tiered access levels**: Create bronze, silver, and gold groups with increasing model capabilities and costs.

## Automation and Integration

While Control Layer doesn't directly integrate with identity providers for group management, you can:

- Document group membership policies
- Establish processes for access requests
- Create naming conventions that map to your organization structure
- Implement regular access reviews

## Troubleshooting Access

**User can't see expected models**: Verify group membership and that models are assigned to those groups. Check that models are currently available.

**User has unexpected access**: Review all group memberships. Users might belong to groups you didn't expect.

**Bulk access changes needed**: Plan group structure changes carefully. Consider creating new groups and migrating users rather than modifying existing groups.

## Best Practices

**Start simple**: Begin with a basic group structure and expand as needed. Over-engineering initially creates unnecessary complexity.

**Document everything**: Maintain documentation about group purposes, membership criteria, and assigned models.

**Regular reviews**: Schedule periodic access reviews to ensure permissions remain appropriate.

**Clear naming**: Use descriptive group names that indicate purpose or membership criteria.

**Minimize admin users**: Limit administrator privileges to those who truly need them.

**Plan for growth**: Design group structures that can scale with your organization.
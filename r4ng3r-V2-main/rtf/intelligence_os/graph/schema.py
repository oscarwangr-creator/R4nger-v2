ENTITY_TYPES = ['Person', 'Username', 'Email', 'Phone', 'Domain', 'IP', 'Organization', 'Location', 'Account']
RELATIONSHIP_TYPES = ['owns', 'uses', 'connected_to', 'registered_with', 'located_at']
GRAPH_SCHEMA = {
    'entities': ENTITY_TYPES,
    'relationships': RELATIONSHIP_TYPES,
    'neo4j_constraints': [
        'CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE',
        'CREATE INDEX entity_type IF NOT EXISTS FOR (n:Entity) ON (n.entity_type)',
    ],
}

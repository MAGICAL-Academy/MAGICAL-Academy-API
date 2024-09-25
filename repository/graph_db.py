from neo4j import GraphDatabase

class GraphDB:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def create_story(self, story_id):
        with self.driver.session() as session:
            session.run(
                "CREATE (s:Story {id: $story_id})",
                story_id=story_id
            )

    def create_node(self, story_id, content, is_choice_point=False):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (s:Story {id: $story_id}) "
                "CREATE (n:Node {content: $content, is_choice_point: $is_choice_point}) "
                "CREATE (s)-[:HAS_NODE]->(n) "
                "RETURN id(n) as node_id",
                story_id=story_id,
                content=content,
                is_choice_point=is_choice_point
            )
            return result.single()["node_id"]

    def create_edge(self, from_node_id, to_node_id, relationship_name):
        with self.driver.session() as session:
            session.run(
                "MATCH (a:Node), (b:Node) "
                "WHERE id(a) = $from_node_id AND id(b) = $to_node_id "
                "CREATE (a)-[:%s]->(b)" % relationship_name.replace(" ", "_"),
                from_node_id=from_node_id,
                to_node_id=to_node_id
            )

    def get_story_context(self, story_id):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (s:Story {id: $story_id})-[:HAS_NODE]->(n:Node) "
                "RETURN n.content ORDER BY id(n)",
                story_id=story_id
            )
            context = "\n".join([record["n.content"] for record in result])
            return context

    def close(self):
        self.driver.close()

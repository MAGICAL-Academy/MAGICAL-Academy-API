from neo4j import GraphDatabase

class GraphDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(f"neo4j+s://{uri}", auth=(user, password))

    def close(self):
        self.driver.close()

    def create_story(self, story_id):
        with self.driver.session() as session:
            session.run("CREATE (s:Story {id: $story_id}) RETURN s", story_id=story_id)

    def create_node(self, story_id, content, is_choice_point):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (s:Story {id: $story_id}) "
                "CREATE (n:Node {content: $content, is_choice_point: $is_choice_point}) "
                "CREATE (s)-[:HAS_NODE]->(n) RETURN id(n) AS node_id",
                story_id=story_id, content=content, is_choice_point=is_choice_point)
            return result.single()["node_id"]

    def create_edge(self, from_node_id, to_node_id, choice_text):
        with self.driver.session() as session:
            session.run(
                "MATCH (from:Node), (to:Node) "
                "WHERE id(from) = $from_node_id AND id(to) = $to_node_id "
                "CREATE (from)-[:CHOICE {text: $choice_text}]->(to)",
                from_node_id=from_node_id, to_node_id=to_node_id, choice_text=choice_text)

    def get_choices(self, node_id):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n:Node)-[r:CHOICE]->(m:Node) "
                "WHERE id(n) = $node_id RETURN r.text AS choice, id(m) AS next_node_id",
                node_id=node_id)
            return [{"choice_text": record["choice"], "next_node_id": record["next_node_id"]} for record in result]

    def get_story_context(self, story_id):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (s:Story {id: $story_id})-[:HAS_NODE]->(n) "
                "RETURN collect(n.content) AS context", story_id=story_id)
            return result.single()["context"]

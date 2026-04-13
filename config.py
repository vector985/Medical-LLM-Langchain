GRAPH_TEMPLATE = {
    'desc': {
        'slots': ['disease'],
        'question': 'What is %disease%? / How is %disease% defined?',
        'cypher': "MATCH (n:Disease) WHERE n.name='%disease%' RETURN n.desc AS RES",
        'answer': '[%disease%] Definition: %RES%',
    },
    'cause': {
        'slots': ['disease'],
        'question': 'What causes %disease%? / Why does %disease% happen?',
        'cypher': "MATCH (n:Disease) WHERE n.name='%disease%' RETURN n.cause AS RES",
        'answer': '[%disease%] Causes: %RES%',
    },
    'disease_symptom': {
        'slots': ['disease'],
        'question': 'What symptoms does %disease% have? / What are the clinical manifestations of %disease%?',
        'cypher': "MATCH (n:Disease)-[:DISEASE_SYMPTOM]->(m) WHERE n.name='%disease%' RETURN SUBSTRING(REDUCE(s = '', x IN COLLECT(m.name) | s + ', ' + x), 2) AS RES",
        'answer': '[%disease%] Symptoms: %RES%',
    },
    'symptom': {
        'slots': ['symptom'],
        'question': 'Which diseases may cause the symptom %symptom%?',
        'cypher': "MATCH (n)-[:DISEASE_SYMPTOM]->(m:Symptom) WHERE m.name='%symptom%' RETURN SUBSTRING(REDUCE(s = '', x IN COLLECT(n.name) | s + ', ' + x), 2) AS RES",
        'answer': 'Possible diseases related to [%symptom%]: %RES%',
    },
    'cure_way': {
        'slots': ['disease'],
        'question': 'What medicines may help %disease% recover faster? / How is %disease% treated?',
        'cypher': '''
            MATCH (n:Disease)-[:DISEASE_CUREWAY]->(m1),
                (n:Disease)-[:DISEASE_DRUG]->(m2),
                (n:Disease)-[:DISEASE_DO_EAT]->(m3)
            WHERE n.name = '%disease%'
            WITH COLLECT(DISTINCT m1.name) AS m1Names, 
                COLLECT(DISTINCT m2.name) AS m2Names,
                COLLECT(DISTINCT m3.name) AS m3Names
            RETURN SUBSTRING(REDUCE(s = '', x IN m1Names | s + ', ' + x), 2) AS RES1,
                SUBSTRING(REDUCE(s = '', x IN m2Names | s + ', ' + x), 2) AS RES2,
                SUBSTRING(REDUCE(s = '', x IN m3Names | s + ', ' + x), 2) AS RES3
            ''',
        'answer': '[%disease%] Treatment options: %RES1%.\nPossible medications: %RES2%.\nRecommended foods: %RES3%',
    },
    'cure_department': {
        'slots': ['disease'],
        'question': 'Which department should I visit in the hospital for %disease%?',
        'cypher': "MATCH (n:Disease)-[:DISEASE_DEPARTMENT]->(m) WHERE n.name='%disease%' RETURN SUBSTRING(REDUCE(s = '', x IN COLLECT(m.name) | s + ', ' + x), 2) AS RES",
        'answer': '[%disease%] Recommended department: %RES%',
    },
    'prevent': {
        'slots': ['disease'],
        'question': 'How can %disease% be prevented?',
        'cypher': "MATCH (n:Disease) WHERE n.name='%disease%' RETURN n.prevent AS RES",
        'answer': '[%disease%] Prevention: %RES%',
    },
    'not_eat': {
        'slots': ['disease'],
        'question': 'What dietary restrictions are there for %disease%? / What should patients with %disease% avoid eating?',
        'cypher': "MATCH (n:Disease)-[:DISEASE_NOT_EAT]->(m) WHERE n.name='%disease%' RETURN SUBSTRING(REDUCE(s = '', x IN COLLECT(m.name) | s + ', ' + x), 2) AS RES",
        'answer': 'Foods to avoid for [%disease%]: %RES%',
    },
    'check': {
        'slots': ['disease'],
        'question': 'What tests are typically needed for %disease%?',
        'cypher': "MATCH (n:Disease)-[:DISEASE_CHECK]->(m) WHERE n.name='%disease%' RETURN SUBSTRING(REDUCE(s = '', x IN COLLECT(m.name) | s + ', ' + x), 2) AS RES",
        'answer': '[%disease%] Recommended tests: %RES%',
    },
    'cured_prob': {
        'slots': ['disease'],
        'question': 'Can %disease% be cured? / What is the recovery rate of %disease%?',
        'cypher': "MATCH (n:Disease) WHERE n.name='%disease%' RETURN n.cured_prob AS RES",
        'answer': '[%disease%] Recovery rate: %RES%',
    },
    'acompany': {
        'slots': ['disease'],
        'question': 'What complications can occur with %disease%?',
        'cypher': "MATCH (n:Disease)-[:DISEASE_ACOMPANY]->(m) WHERE n.name='%disease%' RETURN SUBSTRING(REDUCE(s = '', x IN COLLECT(m.name) | s + ', ' + x), 2) AS RES",
        'answer': '[%disease%] Complications: %RES%',
    },
    'indications': {
        'slots': ['drug'],
        'question': 'What diseases can %drug% be used to treat?',
        'cypher': "MATCH (n:Disease)-[:DISEASE_DRUG]->(m:Drug) WHERE m.name='%drug%' RETURN SUBSTRING(REDUCE(s = '', x IN COLLECT(n.name) | s + ', ' + x), 2) AS RES",
        'answer': '[%drug%] Possible indications: %RES%',
    },
}

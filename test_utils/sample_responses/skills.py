# -*- coding: utf-8 -*-
"""
Sample responses for skills data from EMSI service. These will be used in tests.
"""

SKILL_TEXT_DATA = 'Great candidates also have\n\n Experience with a particular JS MV* framework ' \
            '(we happen to use React)\n Experience working with databases\n Experience with AWS' \
            '\n Familiarity with microservice architecture\n Familiarity with modern CSS practices, ' \
            'e.g. LESS, SASS, CSS-in-JS'

SKILLS = {
    'data': [
        {
            'confidence': 1,
            'skill': {
                'id': 'KSDJCA4E89LB98JAZ7LZ',
                'name': 'React.js',
                'infoUrl': 'https://skills.emsidata.com/skills/KSDJCA4E89LB98JAZ7LZ',
                'tags': [
                    {
                        'key': 'wikipediaUrl',
                        'value': 'https://en.wikipedia.org/wiki/React.js'
                    }
                ],
                'type': {
                    'id': 'ST1',
                    'name': 'Hard Skill'
                }
            }
        },
        {
            'confidence': 1,
            'skill': {
                'id': 'KS120FG6YP8PQYYNQY9B',
                'name': 'Amazon Web Services',
                'infoUrl': 'https://skills.emsidata.com/skills/KS120FG6YP8PQYYNQY9B',
                'tags': [
                    {
                        'key': 'wikipediaUrl',
                        'value': 'https://en.wikipedia.org/wiki/Amazon_Web_Services'
                    }
                ],
                'type': {
                    'id': 'ST1',
                    'name': 'Hard Skill'
                }
            }
        },
        {
            'confidence': 1,
            'skill': {
                'id': 'KS121F45VPV8C9W3QFYH',
                'name': 'Cascading Style Sheets (CSS)',
                'infoUrl': 'https://skills.emsidata.com/skills/KS121F45VPV8C9W3QFYH',
                'tags': [
                    {
                        'key': 'wikipediaUrl',
                        'value': 'https://en.wikipedia.org/wiki/Cascading_Style_Sheets_-_CSS'
                    }
                ],
                'type': {
                    'id': 'ST1',
                    'name': 'Hard Skill'
                }
            }
        },
        {
            'confidence': 0.9994209408760071,
            'skill': {
                'id': 'KS1200771D9CR9LB4MWW',
                'name': 'JavaScript (Programming Language)',
                'infoUrl': 'https://skills.emsidata.com/skills/KS1200771D9CR9LB4MWW',
                'tags': [
                    {
                        'key': 'wikipediaUrl',
                        'value': 'https://en.wikipedia.org/wiki/Javascript_(programming_language)'
                    }
                ],
                'type': {
                    'id': 'ST1',
                    'name': 'Hard Skill'
                }
            }
        }
    ]
}

MISSING_NAME_SKILLS = {
    'data': [
        {
            'confidence': 1,
            'skill': {
                'id': 'KSDJCA4E89LB98JAZ7LZ',
                'infoUrl': 'https://skills.emsidata.com/skills/KSDJCA4E89LB98JAZ7LZ',
                'tags': [
                    {
                        'key': 'wikipediaUrl',
                        'value': 'https://en.wikipedia.org/wiki/React.js'
                    }
                ],
                'type': {
                    'id': 'ST1',
                    'name': 'Hard Skill'
                }
            }
        }
    ]
}

TYPE_ERROR_SKILLS = {
    'data': [
        {
            'confidence': 'error-value',
            'skill': {
                'id': 'KSDJCA4E89LB98JAZ7LZ',
                'name': 'React.js',
                'infoUrl': 'https://skills.emsidata.com/skills/KSDJCA4E89LB98JAZ7LZ',
                'tags': [
                    {
                        'key': 'wikipediaUrl',
                        'value': 'https://en.wikipedia.org/wiki/React.js'
                    }
                ],
                'type': {
                    'id': 'ST1',
                    'name': 'Hard Skill'
                }
            }
        }
    ]
}

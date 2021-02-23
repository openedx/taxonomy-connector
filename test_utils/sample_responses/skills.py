# -*- coding: utf-8 -*-
"""
Sample responses for skills data from EMSI service. These will be used in tests.
"""

SKILL_TEXT_DATA = 'Great candidates also have\n\n Experience with a particular JS MV* framework ' \
            '(we happen to use React)\n Experience working with databases\n Experience with AWS' \
            '\n Familiarity with microservice architecture\n Familiarity with modern CSS practices, ' \
            'e.g. LESS, SASS, CSS-in-JS'

SKILLS_EMSI_RESPONSE = {
    "attributions": [
        {
            "name": "Wikipedia",
            "text": "Wikipedia extracts are distributed under the CC BY-SA license "
                    "(https://creativecommons.org/licenses/by-sa/3.0/)"
        }
    ],
    "data": [
        {
            "confidence": 1.0,
            "skill": {
                "id": "KSDJCA4E89LB98JAZ7LZ",
                "infoUrl": "https://skills.emsidata.com/skills/KSDJCA4E89LB98JAZ7LZ",
                "name": "React.js",
                "tags": [
                    {
                        "key": "wikipediaExtract",
                        "value": "React is an open-source, front end, JavaScript library for building user interfaces "
                                 "or UI components. It is maintained by Facebook and a community of individual "
                                 "developers and companies.\nReact can be used as a base in the development of "
                                 "single-page or mobile applications. However, React is only concerned with state "
                                 "management and rendering that state to the DOM, so creating React applications "
                                 "usually requires the use of additional libraries for routing. React Router is an "
                                 "example of such a library."
                    },
                    {
                        "key": "wikipediaUrl",
                        "value": "https://en.wikipedia.org/wiki/React.js"
                    }
                ],
                "type": {
                    "id": "ST1",
                    "name": "Hard Skill"
                }
            }
        },
        {
            "confidence": 1.0,
            "skill": {
                "id": "KSZX7YZWNR5IDR1I2VMZ",
                "infoUrl": "https://skills.emsidata.com/skills/KSZX7YZWNR5IDR1I2VMZ",
                "name": "Microservices",
                "tags": [
                    # missing WikipediaExtract key
                    {
                        "key": "wikipediaUrl",
                        "value": "https://en.wikipedia.org/wiki/Microservices"
                    }
                ],
                "type": {
                    "id": "ST1",
                    "name": "Hard Skill"
                }
            }
        },
        {
            "confidence": 1.0,
            "skill": {
                "id": "KS120FG6YP8PQYYNQY9B",
                "infoUrl": "https://skills.emsidata.com/skills/KS120FG6YP8PQYYNQY9B",
                "name": "Amazon Web Services",
                "tags": [
                    {
                        "key": "wikipediaExtract",
                        "value": "Amazon Web Services (AWS) is a subsidiary of Amazon providing on-demand cloud "
                                 "computing platforms and APIs to individuals, companies, and governments,"
                                 " on a metered pay-as-you-go basis. These cloud computing web services provide a "
                                 "variety of basic abstract technical infrastructure and distributed computing"
                                 " building blocks and tools. One of these services is Amazon Elastic Compute Cloud"
                                 " (EC2), which allows users to have at their disposal a virtual cluster of computers, "
                                 "available all the time, through the Internet. AWS's version of virtual computers "
                                 "emulates most of the attributes of a real computer, including hardware central "
                                 "processing units (CPUs) and graphics processing units (GPUs) for processing; "
                                 "local/RAM memory; hard-disk/SSD storage; a choice of operating systems; networking; "
                                 "and pre-loaded application software such as web servers, databases, and customer "
                                 "relationship management (CRM)."
                    },
                    {
                        "key": "wikipediaUrl",
                        "value": "https://en.wikipedia.org/wiki/Amazon_Web_Services"
                    }
                ],
                "type": {
                    "id": "ST1",
                    "name": "Hard Skill"
                }
            }
        },
        {
            "confidence": 1.0,
            "skill": {
                "id": "KS121F45VPV8C9W3QFYH",
                "infoUrl": "https://skills.emsidata.com/skills/KS121F45VPV8C9W3QFYH",
                "name": "Cascading Style Sheets (CSS)",
                "tags": [
                    {
                        "key": "wikipediaExtract",
                        "value": "Cascading Style Sheets (CSS) is a style sheet language used for describing"
                                 " the presentation of a document written in a markup language such as HTML. CSS"
                                 " is a cornerstone technology of the World Wide Web, alongside HTML and JavaScript."
                    },
                    {
                        "key": "wikipediaUrl",
                        "value": "https://en.wikipedia.org/wiki/Cascading_Style_Sheets_-_CSS"
                    }
                ],
                "type": {
                    "id": "ST1",
                    "name": "Hard Skill"
                }

            }
        },

    ]
}

SKILLS_EMSI_CLIENT_RESPONSE = {
    "attributions": [
        {
            "name": "Wikipedia",
            "text": "Wikipedia extracts are distributed under the CC BY-SA license "
                    "(https://creativecommons.org/licenses/by-sa/3.0/)"
        }
    ],
    "data": [
        {
            "confidence": 1.0,
            "skill": {
                "id": "KSDJCA4E89LB98JAZ7LZ",
                "infoUrl": "https://skills.emsidata.com/skills/KSDJCA4E89LB98JAZ7LZ",
                "name": "React.js",
                "tags": [
                    {
                        "key": "wikipediaExtract",
                        "value": "React is an open-source, front end, JavaScript library for building user interfaces "
                                 "or UI components. It is maintained by Facebook and a community of individual "
                                 "developers and companies.\nReact can be used as a base in the development of "
                                 "single-page or mobile applications. However, React is only concerned with state "
                                 "management and rendering that state to the DOM, so creating React applications "
                                 "usually requires the use of additional libraries for routing. React Router is an "
                                 "example of such a library."
                    },
                    {
                        "key": "wikipediaUrl",
                        "value": "https://en.wikipedia.org/wiki/React.js"
                    }
                ],
                "type": {
                    "id": "ST1",
                    "name": "Hard Skill"
                },
                "description": "React is an open-source, front end, JavaScript library for building user interfaces "
                               "or UI components. It is maintained by Facebook and a community of individual "
                               "developers and companies.\nReact can be used as a base in the development of "
                               "single-page or mobile applications. However, React is only concerned with state "
                               "management and rendering that state to the DOM, so creating React applications "
                               "usually requires the use of additional libraries for routing. React Router is an "
                               "example of such a library.",
            }
        },
        {
            "confidence": 1.0,
            "skill": {
                "id": "KSZX7YZWNR5IDR1I2VMZ",
                "infoUrl": "https://skills.emsidata.com/skills/KSZX7YZWNR5IDR1I2VMZ",
                "name": "Microservices",
                "tags": [

                    {
                        "key": "wikipediaUrl",
                        "value": "https://en.wikipedia.org/wiki/Microservices"
                    }
                ],
                "type": {
                    "id": "ST1",
                    "name": "Hard Skill"
                },
                "description": "",
            }
        },
        {
            "confidence": 1.0,
            "skill": {
                "id": "KS120FG6YP8PQYYNQY9B",
                "infoUrl": "https://skills.emsidata.com/skills/KS120FG6YP8PQYYNQY9B",
                "name": "Amazon Web Services",
                "tags": [
                    {
                        "key": "wikipediaExtract",
                        "value": "Amazon Web Services (AWS) is a subsidiary of Amazon providing on-demand cloud "
                                 "computing platforms and APIs to individuals, companies, and governments,"
                                 " on a metered pay-as-you-go basis. These cloud computing web services provide a "
                                 "variety of basic abstract technical infrastructure and distributed computing"
                                 " building blocks and tools. One of these services is Amazon Elastic Compute Cloud"
                                 " (EC2), which allows users to have at their disposal a virtual cluster of computers, "
                                 "available all the time, through the Internet. AWS's version of virtual computers "
                                 "emulates most of the attributes of a real computer, including hardware central "
                                 "processing units (CPUs) and graphics processing units (GPUs) for processing; "
                                 "local/RAM memory; hard-disk/SSD storage; a choice of operating systems; networking; "
                                 "and pre-loaded application software such as web servers, databases, and customer "
                                 "relationship management (CRM)."
                    },
                    {
                        "key": "wikipediaUrl",
                        "value": "https://en.wikipedia.org/wiki/Amazon_Web_Services"
                    }
                ],
                "type": {
                    "id": "ST1",
                    "name": "Hard Skill"
                },
                "description": "Amazon Web Services (AWS) is a subsidiary of Amazon providing on-demand cloud "
                               "computing platforms and APIs to individuals, companies, and governments,"
                               " on a metered pay-as-you-go basis. These cloud computing web services provide a "
                               "variety of basic abstract technical infrastructure and distributed computing"
                               " building blocks and tools. One of these services is Amazon Elastic Compute Cloud"
                               " (EC2), which allows users to have at their disposal a virtual cluster of computers, "
                               "available all the time, through the Internet. AWS's version of virtual computers "
                               "emulates most of the attributes of a real computer, including hardware central "
                               "processing units (CPUs) and graphics processing units (GPUs) for processing; "
                               "local/RAM memory; hard-disk/SSD storage; a choice of operating systems; networking; "
                               "and pre-loaded application software such as web servers, databases, and customer "
                               "relationship management (CRM)."
            }
        },
        {
            "confidence": 1.0,
            "skill": {
                "id": "KS121F45VPV8C9W3QFYH",
                "infoUrl": "https://skills.emsidata.com/skills/KS121F45VPV8C9W3QFYH",
                "name": "Cascading Style Sheets (CSS)",
                "tags": [
                    {
                        "key": "wikipediaExtract",
                        "value": "Cascading Style Sheets (CSS) is a style sheet language used for describing"
                                 " the presentation of a document written in a markup language such as HTML. CSS"
                                 " is a cornerstone technology of the World Wide Web, alongside HTML and JavaScript."
                    },
                    {
                        "key": "wikipediaUrl",
                        "value": "https://en.wikipedia.org/wiki/Cascading_Style_Sheets_-_CSS"
                    }
                ],
                "type": {
                    "id": "ST1",
                    "name": "Hard Skill"
                },
                "description": "Cascading Style Sheets (CSS) is a style sheet language used for describing"
                               " the presentation of a document written in a markup language such as HTML. CSS"
                               " is a cornerstone technology of the World Wide Web, alongside HTML and JavaScript.",
            }
        },
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

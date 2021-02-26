# -*- coding: utf-8 -*-
"""
Sample responses for job lookup from EMSI service. These will be used in tests.
"""
JOB_LOOKUP_FILTER = {
    "ids": ["15.0", "15.1"]
}

JOB_LOOKUP = {
    "data": [
        {
            "id": "15.0",
            "name": "Software Engineers",
            "properties": {
                "singular_name": "Software Engineer",
                "soc2": "15-0000",
                "soc2_name": "Computer and Mathematical"
            }
        },
        {
            "id": "15.1",
            "name": "Project Managers (Computer and Mathematical)",
            "properties": {
                "singular_name": "Project Manager (Computer and Mathematical)",
                "soc2": "15-0000",
                "soc2_name": "Computer and Mathematical"
            }
        }
    ]
}

JOB_LOOKUP_MISSING_KEY = {
    "data": [
        {
            "id": "15.0",
            "name": "Software Engineers",
            "properties": {
                # missing `singular_name` key
                "soc2": "15-0000",
                "soc2_name": "Computer and Mathematical"
            }
        },
        {
            "id": "15.1",
            "name": "Project Managers (Computer and Mathematical)",
            "properties": {
                "soc2": "15-0000",
                "soc2_name": "Computer and Mathematical"
            }
        }
    ]
}

import re

SYNONYM_MAP = {
    'react.js': 'react', 'reactjs': 'react',
    'next.js': 'nextjs', 'nextjs': 'nextjs',
    'vue.js': 'vue', 'vuejs': 'vue',
    'angular.js': 'angular', 'angularjs': 'angular',
    'node.js': 'node', 'nodejs': 'node',
    'express.js': 'express', 'expressjs': 'express',
    'nuxt.js': 'nuxt', 'nuxtjs': 'nuxt',
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    'aws': 'aws',
    'amazon web services': 'aws',
    'gcp': 'gcp',
    'google cloud platform': 'gcp',
    'google cloud': 'gcp',
    'azure': 'azure',
    'microsoft azure': 'azure',
    'ci/cd': 'cicd', 'ci cd': 'cicd',
    'continuous integration': 'cicd',
    'continuous integration continuous deployment': 'cicd',
    'continuous integration/continuous deployment': 'cicd',
    'postgresql': 'postgres', 'postgres': 'postgres',
    'mongodb': 'mongodb', 'mongo': 'mongodb', 'mongo db': 'mongodb',
    'rest api': 'rest', 'rest apis': 'rest',
    'restful api': 'rest', 'restful apis': 'rest',
    'graphql api': 'graphql',
    'k8s': 'kubernetes',
    'ml': 'machine learning',
    'ai': 'artificial intelligence',
    'nlp': 'natural language processing',
    'tf': 'tensorflow',
}

SKILL_CLUSTERS = {
    'Frontend': {
        'members': {'react', 'nextjs', 'angular', 'vue', 'svelte',
                    'javascript', 'typescript', 'html', 'css', 'tailwind',
                    'redux', 'webpack', 'vite'},
        'transferable': {
            'react': [('nextjs', 0.9), ('angular', 0.5), ('vue', 0.5)],
            'nextjs': [('react', 0.85)],
            'angular': [('react', 0.5), ('vue', 0.5)],
            'vue': [('react', 0.5), ('angular', 0.5)],
            'javascript': [('typescript', 0.9)],
            'typescript': [('javascript', 0.8)],
        },
    },
    'Backend': {
        'members': {'node', 'express', 'django', 'flask', 'fastapi',
                    'spring', 'laravel', 'rails', 'rest', 'graphql',
                    'grpc', 'microservices', 'serverless'},
        'transferable': {
            'node': [('express', 0.85), ('django', 0.5), ('flask', 0.5)],
            'express': [('node', 0.85), ('fastapi', 0.6), ('flask', 0.6)],
            'django': [('flask', 0.7), ('fastapi', 0.7)],
            'flask': [('fastapi', 0.8), ('django', 0.7)],
            'rest': [('graphql', 0.7), ('grpc', 0.6)],
            'graphql': [('rest', 0.7)],
        },
    },
    'Databases': {
        'members': {'postgres', 'mysql', 'sqlite', 'mongodb', 'redis',
                    'elasticsearch', 'cassandra', 'dynamodb', 'oracle',
                    'mssql', 'mariadb'},
        'transferable': {
            'postgres': [('mysql', 0.8), ('mariadb', 0.8), ('oracle', 0.6), ('mssql', 0.6)],
            'mysql': [('postgres', 0.8), ('mariadb', 0.85), ('sqlite', 0.6)],
            'mongodb': [('dynamodb', 0.6), ('cassandra', 0.5), ('redis', 0.5)],
            'redis': [('elasticsearch', 0.5), ('mongodb', 0.4)],
            'dynamodb': [('mongodb', 0.6), ('cassandra', 0.55)],
        },
    },
    'Cloud & DevOps': {
        'members': {'aws', 'gcp', 'azure', 'docker', 'kubernetes', 'cicd',
                    'jenkins', 'github actions', 'terraform', 'ansible',
                    'helm', 'linux', 'nginx', 'prometheus', 'grafana'},
        'transferable': {
            'aws': [('gcp', 0.7), ('azure', 0.7)],
            'gcp': [('aws', 0.7), ('azure', 0.7)],
            'azure': [('aws', 0.7), ('gcp', 0.7)],
            'docker': [('kubernetes', 0.7)],
            'kubernetes': [('docker', 0.7)],
            'cicd': [('jenkins', 0.75), ('github actions', 0.75)],
            'jenkins': [('cicd', 0.8), ('github actions', 0.7)],
        },
    },
    'Programming Languages': {
        'members': {'python', 'javascript', 'typescript', 'java', 'kotlin',
                    'scala', 'go', 'rust', 'ruby', 'php', 'cpp', 'csharp',
                    'swift', 'r'},
        'transferable': {
            'python': [('r', 0.4)],
            'javascript': [('typescript', 0.9)],
            'typescript': [('javascript', 0.85)],
            'java': [('kotlin', 0.85), ('scala', 0.6), ('csharp', 0.5)],
            'kotlin': [('java', 0.85), ('scala', 0.5)],
            'go': [('rust', 0.5), ('java', 0.4)],
        },
    },
    'Data & ML': {
        'members': {'machine learning', 'deep learning', 'tensorflow',
                    'pytorch', 'keras', 'scikit', 'pandas', 'numpy',
                    'spark', 'hadoop', 'tableau', 'powerbi', 'data analysis',
                    'data science', 'nlp', 'computer vision'},
        'transferable': {
            'tensorflow': [('pytorch', 0.85), ('keras', 0.8)],
            'pytorch': [('tensorflow', 0.85), ('keras', 0.75)],
            'machine learning': [('deep learning', 0.8), ('data science', 0.8)],
            'pandas': [('numpy', 0.7), ('spark', 0.6)],
        },
    },
    'Testing & Quality': {
        'members': {'jest', 'mocha', 'pytest', 'junit', 'selenium',
                    'cypress', 'playwright', 'testing', 'unit testing',
                    'integration testing', 'tdd', 'bdd'},
        'transferable': {
            'jest': [('mocha', 0.8), ('pytest', 0.5)],
            'cypress': [('playwright', 0.85), ('selenium', 0.7)],
            'pytest': [('junit', 0.7), ('jest', 0.5)],
            'tdd': [('bdd', 0.75), ('testing', 0.8)],
        },
    },
}

SECTION_PATTERNS = {
    'experience': re.compile(
        r'(work\s*experience|professional\s*experience|employment|experience)', re.I),
    'education': re.compile(
        r'(education|academic|qualification|degree|university|college)', re.I),
    'skills': re.compile(
        r'(skills|technical\s*skills|core\s*competencies|technologies|tech\s*stack)', re.I),
    'projects': re.compile(
        r'(projects?|personal\s*projects?|academic\s*projects?)', re.I),
    'certifications': re.compile(
        r'(certifications?|certificates?|licenses?|credentials?)', re.I),
    'summary': re.compile(
        r'(summary|objective|profile|about\s*me|career\s*objective)', re.I),
}

SECTION_WEIGHTS = {
    'skills': 0.35,
    'experience': 0.35,
    'projects': 0.20,
    'education': 0.05,
    'certifications': 0.05,
}

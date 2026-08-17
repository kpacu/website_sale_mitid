{
    'name': 'Danish MitID Age Gate for Alcohol (E-Commerce)',
    'version': '19.0.1.0.0',
    'category': 'Website/eCommerce',
   'summary': 'Conditional MitID age-verification at checkout for alcohol categories under Danish NSIS regulations.',
    'description': """
        Danish MitID Age Gate for Alcohol Sales.
        Ensures compliance with age-verification requirements before payment processing.
    """,
    'license': 'OPL-1',
    'price': 0,
    'currency': 'EUR',
    'author': 'IntelligentSolutions',
    'website': 'https://github.com/kpacu/website_sale_mitid',
    'support': 'krassi.dimitrof.com',
    'depends': ['base', 'website', 'website_sale'],
    'data': [
        'views/templates.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}

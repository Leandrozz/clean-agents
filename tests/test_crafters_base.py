def test_crafters_package_importable():
    import clean_agents.crafters
    import clean_agents.crafters.validators
    import clean_agents.crafters.skill
    assert clean_agents.crafters is not None

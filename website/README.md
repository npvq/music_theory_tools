## Architectural Notes

Applications:
- `pages`: for storing basic pages. There might be a `blog` app in the future as well
- `fourpart`: for four-part computing functionalities (testing)
- `polls`: 

## Technical Notes

Reference: [Official Django Documentation Tutorial](https://docs.djangoproject.com/en/4.1/intro/tutorial01/)

The `polls` Django app is just meant to be a test for the Django backend.

Choices of database: https://www.nickmccullum.com/best-database-django-web-apps/
PostgreSQL tutorial: https://medium.com/cloud-tidbits/setup-django-with-postgres-app-on-macos-for-django-tutorials-22ed4dabfaf4
(`pip install psycopg2-binary`)

Find django source files (to find templates to override): `python -c "import django; print(django.__path__)"`

**Todos:**
- [ ] User authentication!
- [ ] Database integration with `fourpart`
- [ ] TailwindCSS integration and basic templates.
- [ ] Learn how to write tests (automated testing) from [Django Tutorial](https://docs.djangoproject.com/en/4.1/intro/tutorial05/).
- [ ] Customize 404/500 page: [Stack Overflow](https://stackoverflow.com/questions/17662928/django-creating-a-custom-500-404-error-page).
describe('Test registration', function () {
    const testUserEmail = "daniel@cache.sh";
    const testUserPassword = "password";
    const testUserNewPassword = "newpassword";

    before(() => {
        const setup = "source scripts/init.sh && cd django_app && DJANGO_SETTINGS_MODULE=settings.test PG_USER=hearo_production PG_HOST=localhost";
        // reset and seed the database prior to every test
        // test with test seed
        cy.exec(`${setup} pg_kill_connections hearo_test`);
        cy.exec(`${setup} ./manage.py reset_db --noinput`);
        cy.exec(`${setup} ./manage.py migrate --noinput`);
        cy.exec(`${setup} ./manage.py loaddata tests/fixtures/sites.json tests/fixtures/seed.json`);
    });
    beforeEach(() => {
        cy.visit('/join/');
        cy.get('#id_email').type(testUserEmail);
        cy.get('#id_password').type(testUserPassword);
        cy.get('#submit-login').click();
        cy.location('pathname').should('eq', '/');
    });
    it('goes to account and change to artist', function(){
    });
    // it('goes to music and sign artist agreement', function(){
    // });
    // it('goes to music and uploads a song', function(){
    // });
    // it('goes to visuals and uploads and image', function(){
    // });
    // it('goes to pages and creates a page', function(){
    // });
    it.only('goes to privacy tab and changes password then logs in again', function(){
        cy.visit('/my-account/privacy/');
        cy.get('#id_curpass').type(testUserPassword);
        cy.get('#id_pass').type(testUserNewPassword);
        cy.get('#id_pass2').type(testUserNewPassword);
        cy.get('#change-password').click().location('pathname').should('eq', '/join/');
    });
});

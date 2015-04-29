%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           nuancier
Version:        0.8.2
Release:        1%{?dist}
Summary:        A web-based voting application for wallpapers

License:        GPLv2+
URL:            https://github.com/fedora-infra/nuancier
Source0:        https://fedorahosted.org/releases/n/u/nuancier/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-flask
BuildRequires:  python-wtforms
BuildRequires:  python-flask-wtf
BuildRequires:  python-fedora >= 0.3.33
BuildRequires:  python-fedora-flask >= 0.3.33
BuildRequires:  python-setuptools
BuildRequires:  python-dogpile-cache
BuildRequires:  python-nose
BuildRequires:  python-coverage

# EPEL6
%if ( 0%{?rhel} && 0%{?rhel} == 6 )
BuildRequires:  python-sqlalchemy0.7
BuildRequires:  python-imaging
Requires:  python-sqlalchemy0.7
Requires:  python-imaging
%else
BuildRequires:  python-sqlalchemy > 0.5
BuildRequires:  python-pillow
Requires:  python-sqlalchemy > 0.5
Requires:  python-pillow
%endif

Requires:  python-flask
Requires:  python-wtforms
Requires:  python-flask-wtf
Requires:  python-fedora >= 0.3.32.3-3
Requires:  python-fedora-flask
Requires:  python-dogpile-cache
Requires:  python-setuptools
Requires:  fedmsg
Requires:  mod_wsgi

%description
Nuancier is a web application for voting for the supplementary
wallpapers that are included in Fedora at each release.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Install apache configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
install -m 644 utility/nuancier.conf $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/nuancier.conf

# Install nuancier configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/nuancier
install -m 644 utility/nuancier.cfg.sample $RPM_BUILD_ROOT/%{_sysconfdir}/nuancier/nuancier.cfg

# Install nuancier wsgi file
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/nuancier
install -m 644 utility/nuancier.wsgi $RPM_BUILD_ROOT/%{_datadir}/nuancier/nuancier.wsgi
install -m 644 createdb.py $RPM_BUILD_ROOT/%{_datadir}/nuancier/nuancier_createdb.py

# Install the alembic files
install -m 644 utility/alembic.ini.sample $RPM_BUILD_ROOT/%{_sysconfdir}/nuancier/alembic.ini
cp -r alembic/ $RPM_BUILD_ROOT/%{_datadir}/nuancier/


%check
./runtests.sh -v -x


%files
%doc README.rst COPYING doc/
%dir %{_sysconfdir}/nuancier/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/nuancier.conf
%config(noreplace) %{_sysconfdir}/nuancier/nuancier.cfg
%config(noreplace) %{_sysconfdir}/nuancier/alembic.ini
%{_datadir}/nuancier/
%{python_sitelib}/nuancier/
%{python_sitelib}/nuancier*.egg-info


%changelog
* Wed Apr 29 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.8.2-1
- Update to 0.8.2
- Fix the graph on the stats page

* Wed Apr 29 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.8.1-1
- Update to 0.8.1
- Improve documentation for new contributors
- Make the Results and Stats links more distringuisable (Shagufta)
- Make nuancier prettier on high resolution display
- Add fedmenu

* Tue Feb 24 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.8.0-1
- Update to 0.8.0
- Create a group of reviewers that can approve/deny candidates
- Create a group of users having weighted votes (their votes count double)
- Fix the form to automatically add the red '*' when the field is mandatory
- Redirect the user when os.mkdir fails
- Drop some css instructions breaking the elections tab/pages
- Improve the configuration documentation
- Add URL to come back to the page you're at when login in/out
- Fix the query retrieving the denied candidate

* Tue Aug 26 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.7.0-1
- Update to 0.7.0
- Fix error message when no election are opened for submission
- Order the candidates in the review page by their date of creation
- Handle the possibility that generating thumbnails fails for one of the image,
  keep generating the others though
- Allow the admin to filter the candidates in the review page by their status
  (Approved, Denied/Pending)
- Activate the session time-out
- Add possibility for user to update candidate that have been denied
- Let the admins see the review page as read-only once the submission period has
  ended
- Rework the result page to show a limit between the candidates that have been
  elected and those that were not

* Wed Jul 16 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.6.0-1
- Update 0.6.0
- Update the documentation (Thanks Michael Haynes and Chaoyi Zha)
- Add comment on the stats page about the possibility to hover over the bars
  of the graph
- Fix https/proxy settings

* Wed Jun 18 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.5.0-2
- Fix changelog entry for 0.5.0-1
- Run tests at build time in the %%check section

* Tue May 13 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.5.0-1
- Update to 0.5.0
- Store the email of the submitter
- Fix sending emails

* Sun May 04 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.3-1
- Update to 0.4.3
- Fix bug when sending email about a rejected candidate

* Sat May 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.2-1
- Update to 0.4.2
- Fix redirect bug

* Tue Apr 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.1-1
- Update to 0.4.1
- Fix the graph/barplot in the stats page/template
- Provide in the stats page the total number of candidates as well as the number
  of approved candidates

* Tue Apr 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.0-1
- Update to 0.4.0
- Improve stats page
- Fix election table on the elections page

* Wed Feb 26 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.3.0-1
- Update to 0.3.0
- fedmsg integration

* Sat Feb 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.0-1
- Rename from nuancier-lite to nuancier
- Adjust all the configuration file name accordingly

* Mon Oct 14 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.2-1
- Update to 0.1.2
- Make the result stat page public
- Couple of bugfixes

* Mon Sep 30 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Update to 0.1.0
- Bugfixes on the vote
- CSS bugfixes
- Add dependency to dogpile.cache

* Sat Sep 21 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.3-1
- Update to version 0.0.3
- Incoporate changes from Ryan Lerch on the voting

* Fri Sep 20 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.2-1
- Update to version 0.0.2 (bugfixes)
- Add Requires to fedmsg

* Fri Sep 20 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.1-1
- Initial packaging work for Fedora


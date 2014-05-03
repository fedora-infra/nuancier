%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           nuancier
Version:        0.4.2
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


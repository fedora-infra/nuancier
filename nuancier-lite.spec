%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           nuancier-lite
Version:        0.0.2
Release:        1%{?dist}
Summary:        A light weight voting app for wallpapers

License:        GPLv2+
URL:            https://github.com/fedora-infra/nuancier-lite
Source0:        https://fedorahosted.org/releases/f/e/fedocal/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-flask
BuildRequires:  python-wtforms
BuildRequires:  python-flask-wtf
BuildRequires:  python-fedora >= 0.3.32.3-3
BuildRequires:  python-fedora-flask

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
Requires:  fedmsg
Requires:  mod_wsgi

%description
Nuancier-lite is a light weight web application for voting for the supplementary
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
install -m 644 nuancier-lite.conf $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/nuancier-lite.conf

# Install nuancier configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/nuancier
install -m 644 nuancier-lite.cfg.sample $RPM_BUILD_ROOT/%{_sysconfdir}/nuancier/nuancier-lite.cfg

# Install nuancier wsgi file
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/nuancier
install -m 644 nuancier.wsgi $RPM_BUILD_ROOT/%{_datadir}/nuancier/nuancier-lite.wsgi
install -m 644 createdb.py $RPM_BUILD_ROOT/%{_datadir}/nuancier/nuancier-lite_createdb.py

%files
%doc README.rst COPYING doc/
%dir %{_sysconfdir}/nuancier/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/nuancier-lite.conf
%config(noreplace) %{_sysconfdir}/nuancier/nuancier-lite.cfg
%{_datadir}/nuancier/
%{python_sitelib}/nuancier/
%{python_sitelib}/nuancier*.egg-info


%changelog
* Fri Sep 20 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.2-1
- Update to version 0.0.2 (bugfixes)
- Add Requires to fedmsg

* Fri Sep 20 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.1-1
- Initial packaging work for Fedora


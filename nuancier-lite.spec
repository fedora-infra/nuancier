%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           nuancier-lite
Version:        0.1.0
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

# Install wsgi, apache configuration and nuancier configuration files
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
install -m 644 nuancier-lite.conf $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/nuancier-lite.conf

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/nuancier
install -m 644 nuancier-lite.cfg.sample $RPM_BUILD_ROOT/%{_sysconfdir}/nuancier/nuancier-lite.cfg

mkdir -p $RPM_BUILD_ROOT/%{_datadir}/nuancier
install -m 644 nuancier.wsgi $RPM_BUILD_ROOT/%{_datadir}/nuancier/nuancier.wsgi

%files
%doc README.rst COPYING doc/
%doc createdb.py
%config(noreplace) %{_sysconfdir}/httpd/conf.d/nuancier-lite.conf
%config(noreplace) %{_sysconfdir}/nuancier/nuancier-lite.cfg
%dir %{_sysconfdir}/nuancier/
%{_datadir}/nuancier/
%{python_sitelib}/nuancier/
%{python_sitelib}/nuancier*.egg-info

%changelog
* Tue Sep 03 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Initial packaging work for Fedora


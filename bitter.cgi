#!/usr/bin/perl -w

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use CGI::Cookie;

sub main() {
	
	$dataset_size = "medium"; 
	$users_dir = "dataset-$dataset_size/users";
	%users = ();
	%bleats = ();
	$debug = 1;
	$submit = param('submit');
	$svalue = param('svalue');
	$page = param('page');
	
	my $username = param('Username') || undef;
	my $password = param('Password') || undef;
	my $loginSuccess = "";
	if (defined $username && defined $password) {
		$loginSuccess = checkUser($username, $password); #authenticates the user and if successful, creates a cookie and sends it via header()
		CGI->delete('Username');				 #also prints header() regardless of success or fail
		CGI->delete('Password');
	} elsif ($submit eq "Logout") {  		     
		$loginSuccess = logout();			     #clears all cookie values, and expires them, then sends them via header()
		CGI->delete('submit','svalue','page');
		CGI->delete('submit','svalue','page');
	} else { 				 				     #prints a header in case the previous if statements didn't execute
		print header();
	}

	# print start of HTML ASAP to assist debugging if there is an error in the script
	page_header();
	# Now tell CGI::Carp to embed any warning in HTML
	warningsToBrowser(1);
	%cookie = CGI::Cookie->fetch;
	if ($cookie{'Username'} && $cookie{'Password'}) {
		$username = $cookie{'Username'}->value;
		$password = $cookie{'Password'}->value;
	} 
	
	if ((defined $username && defined $password) && !($submit eq "Logout")) {
		navbar_logout();
	} else {
		navbar();
	}

	newBleat();
	print "submit = $submit\n"."username = $username\n"."password = $password\n"."loginsuccess = $loginSuccess\n";
	
	if (defined $page) {
#		print login_button();
		print searchBar();
		print searchResult($page);
		print page_trailer();
	} elsif (($submit eq "Search")&&(defined $svalue)) {
		print search();
    } elsif ($submit eq "Login") {
        login();
	} elsif ($loginSuccess eq "false login") {
		param(-name=>'submit', -values=>'Login');
		print "Invalid Username or Password\n";
		print '<p>';
		login();
	} elsif ($submit eq "Send Bleat") {
		send_bleat_page();
	} elsif (($newBleatSuccess eq "false")) {
		param(-name=>'submit', -values=>'Send Bleat');
		print "Invalid bleat\n";
		print '<p>';
		send_bleat_page();
	} elsif ($loginSuccess eq "logout") {
		print searchBar();
		print user_page();
		print page_trailer();
		CGI->delete('submit','svalue','page');
	} elsif ((defined $username && defined $password) || ($loginSuccess eq "login")) {
		print searchBar();
		print send_bleat_button();
		print page($username);
		print page_trailer();
	} else {
   #    print login_button();
		print searchBar();
		print user_page();
		print page_trailer();
	}
}

sub logout() {
	my $success = "logout";
	my $c = CGI::Cookie->new(-name =>'Username',
                          -value=>'',
                          -expires =>  '-1d');
	my $d = CGI::Cookie->new(-name =>'Password',
                          -value=>'',
                          -expires =>'-1d');
	print header(-cookie=>[$c,$d]);
	return $success;
}

sub page() {
	my ($page) = @_;
    my $user_to_show  = "$users_dir/$page/";
    my $details_filename = "$user_to_show/details.txt";
	
	open my $p, "$details_filename" or die "can not open $details_filename: $!";
    my @userDetails = <$p>;	
	foreach my $line (@userDetails) {
		chomp($line);
		if ($line =~ /^username: (\w+)/) {
			my $username = $1;
			$users{$user_to_show}{user_name} = $username;
		} elsif ($line =~ /^full_name:/) {
			$line =~ s/full_name: //;
			$users{$user_to_show}{full_name} = $line;
		} elsif ($line =~ /^home_suburb:/) {
			$line =~ s/home_suburb: //;
			$users{$user_to_show}{home_suburb} = $line;
		} elsif ($line =~ /^listens:/) {
			$line =~ s/^listens: //;
			@arr = split / /, $line;
			my $string = "";
			$string = join(" \n\t", @arr);
			$users{$user_to_show}{listens} = $string;
		}
	}
	my $user_info = "";
	$user_info = "Full Name: $users{$user_to_show}{full_name}\nUsername: $users{$user_to_show}{user_name}\nSuburb: $users{$user_to_show}{home_suburb}\nListens to:\n\t$users{$user_to_show}{listens}\n";
	
	my $bleats_filename = "$user_to_show/bleats.txt"; 
	open my $f, "$bleats_filename" or die "can not open $bleats_filename: $!";
	my @userBleats = <$f>;
	foreach my $bleat (@userBleats) {
		open $b, "dataset-$dataset_size/bleats/$bleat" or die "can not open bleats_dir/$bleat: $!";
		my @bleatContents = <$b>;
		foreach my $bl (@bleatContents) {
			chomp($bl);
			if ($bl =~ /^time: /) {
				$bl =~ s/^time: //;
				$bleats{$bleat}{"time"} = $bl;
			} elsif ($bl =~ /^bleat: /) {
				$bl =~ s/^bleat: //;
				$bleats{$bleat}{"bleat"} = $bl;
			} 
		}
	}	
	
	my @listenBleats = ();
	foreach my $listen (@arr) {
		print "listen = $listen\n";
		$bleats_filename = "$users_dir/$listen/bleats.txt";
		open my $l, "$bleats_filename" or die "can not open $bleats_filename: $!";
		@listenBleats = <$l>;
		foreach $bleat (@listenBleats) {
			open $b, "dataset-$dataset_size/bleats/$bleat" or die "can not open bleats_dir/$bleat: $!";
			@bleatContents = <$b>;
			foreach $bl (@bleatContents) {
				chomp($bl);
				if ($bl =~ /^time: /) {
					$bl =~ s/^time: //;
					$bleats{$bleat}{"time"} = $bl;
				} elsif ($bl =~ /^bleat: /) {
					$bl =~ s/^bleat: //;
					$bleats{$bleat}{"bleat"} = $bl;
				}	 
			}
		}
	}
	
	my @allBleats = sort(glob("dataset-$dataset_size/bleats/*"));
	my %temp = "";
	my $tag = "\@$page";
	my $success = "";
	foreach $bleat (@allBleats) {
		open my $t, "$bleat" or die "can not open $bleat: $!";
		@tagBleats = <$t>;
		$success = 0;
		my $bleat_dir = "dataset-$dataset_size/bleats/";
		$bleatID = $bleat;
		$bleatID =~ s/$bleat_dir//;
		foreach $bl (@bleatContents) {
			chomp($bl);
			if ($bl =~ /^time: /) {
				$bl =~ s/^time: //;
				$temp{"time"} = $bl;
			} elsif ($bl =~ /^bleat: /) {
				$bl =~ s/^bleat: //;
				$temp{"bleat"} = $bl;
				if ($bl =~ /$tag/) {
					$success = 1;
					last;
				}
			}
		}
		if ($success == 1) {
			$bleats{$bleatID}{"time"} = $temp{"time"};				
			$bleats{$bleatID}{"bleat"} = $temp{"bleat"};
		}	 	
	}
	
	close $t;
	close $p;
	close $b;	
	close $l;
	close $f;
	
	$bleat_info = "Displaying all bleats:";
	foreach my $key (sort { $bleats{$b}{time} <=> $bleats{$a}{time} } keys %bleats) {
		$bleat_info = join(" \n", $bleat_info, $bleats{$key}{"bleat"});
	}
    return div({-class => "bitter_user_details"}, "\n", img({-src => "$user_to_show/profile.jpg", -alt => ""}), 
		"\n$user_info\n"), div({-class => "bitter_bleats"}, "\n$bleat_info\n\n"), "\n",
        '<p>';
}

sub searchResult() {
	my ($page) = @_;
    my $user_to_show  = "$users_dir/$page/";
    my $details_filename = "$user_to_show/details.txt";
    open my $p, "$details_filename" or die "can not open $details_filename: $!";
    @userDetails = <$p>;	
	foreach my $line (@userDetails) {
		chomp($line);
		if ($line =~ /^username: (\w+)/) {
			my $username = $1;
			$users{$user_to_show}{user_name} = $username;
		} elsif ($line =~ /^full_name:/) {
			$line =~ s/full_name: //;
			$users{$user_to_show}{full_name} = $line;
		} elsif ($line =~ /^home_suburb:/) {
			$line =~ s/home_suburb: //;
			$users{$user_to_show}{home_suburb} = $line;
		} elsif ($line =~ /^listens:/) {
			$line =~ s/^listens: //;
			my @arr = split / /, $line;
			my $string = "";
			$string = join(" \n\t", @arr);
			$users{$user_to_show}{listens} = $string;
		}
	}
	my $user_info = "";
	$user_info = "Full Name: $users{$user_to_show}{full_name}\nUsername: $users{$user_to_show}{user_name}\nSuburb: $users{$user_to_show}{home_suburb}\nListens to:\n\t$users{$user_to_show}{listens}\n";
    close $p;
    return div({-class => "bitter_user_details"}, "\n", img({-src => "$user_to_show/profile.jpg", -alt => ""}), 
		"\n$user_info\n"), "\n",
        '<p>';
}

sub search() {
	my @users = sort(glob("$users_dir/*"));
	$success = 0;
	@matches = ();
	foreach my $file (@users) {
		my $details_filename = "$file/details.txt";
		open my $p, "$details_filename" or die "can not open $details_filename: $!";
		@details = <$p>;
		foreach my $line (@details) {
			chomp($line);
			if ($line =~ /^username: (\w+)/) {
				my $username = $1;
				if ($username =~ /$svalue/i) {
					$success = 1;
                    $user = $file;
                    $user =~ s/$users_dir\///;
					push (@matches, $user);
					last;
				}
			} elsif ($line =~ /^full_name:/) {
				$line =~ s/^full_name: //;
				if ($line =~ /$svalue/i) {
					$success = 1;
                    $user = $file;
                    $user =~ s/$users_dir\///;
					push (@matches, $user);
					last;
				}
			}
		}
	}
	close $p;
	print <<eof;
	<div class="bitter_send">
	Displaying search results:
	</div>
eof
	if ($success == "0") {
		return "Your search returned 0 matches\n", "<p>", searchBar(), page_trailer();
	} else {
		my $string = "";
		foreach my $match (@matches) {
			my $user_jpg = "$users_dir/$match/profile.jpg";
            $string .= <<eof;
            <tr class="bitter_tableRow"><td class="bitter_tableRow"> 
            <a href="bitter.cgi?page=$match"> 
            <img src="$user_jpg" alt="" width="100" height="100">        
            $match 
            </a>         
            </td> </tr>
eof
		}
        $toReturn = <<eof;
            <div class="bitter_bleats">
                <table class="bitter_tableRow">
            $string
            </table>
            </div>
eof
		return searchBar().$toReturn.page_trailer();
	}
}

sub checkUser() {
	my ($name, $password) = @_;
	my $success = 0;
    my $details_filename = "$users_dir/$name/details.txt";
	open my $p, "$details_filename" or die "can not open $details_filename: $!";
	@userDetails = <$p>;
	foreach my $line (@userDetails) {
		chomp($line);
		if ($line =~ /^password: /) {
			$line =~ s/^password: //;
			if ($password eq $line) {
				$success = 1;
				last;
			}
		}
	}
	if ($success == 1) {
		my $c = CGI::Cookie->new(-name =>'Username',
                          -value=>$name,
                          -expires =>  '+1M');
		my $d = CGI::Cookie->new(-name => 'Password',
                          -value=>$password,
                          -expires =>'+1M');
		print header(-cookie=>[$c,$d]);
		$success = "login";
		return $success;
	} else {
		print header();
		$success = "false login";
		return $success;
	}
}

sub send_bleat_page() {
	print <<eof;
	<div class="bitter_send">
	Send bleat
	</div>
eof
	print '<p>';
	print start_form(-method=>'POST', -action=>"bitter.cgi");
	print textfield(-name=>'send_bleat', -value=>"", -size=>150, -class=>"bitter_textfield", -maxlength=>142, -border=>#FFFFFF, 
		-border-radius=>5);
	print '<p>';
	print "<i>add @ to mark username, add # for keywords </i>";
	print '<p>';
	print submit({-class =>"bitter_send_button", -name=>'bleat_sent', -value=>"Send"});
	print reset({-class =>"bitter_reset_button"});
	print end_form(), <p>;
}	

sub newBleat {
	my $bleat_sent = param('bleat_sent') || undef;
	my $new_bleat_data = param('send_bleat') || undef;
	my $newBleatSuccess = "";
	if (($bleat_sent eq "Send") && !(defined $new_bleat_data)) {
		$newBleatSuccess = "false";
	} elsif (($bleat_sent eq "Send") && (defined $username) && (defined $password) && (defined $new_bleat_data)) {	
		my $new = $new_bleat_data;
		my $secs = time();
		my $epoch = time() + 3000000000;
	
		open my $b, ">dataset-$dataset_size/bleats/$epoch"  or die "can not open dataset-$dataset_size/bleats/$epoch: $!";
		print $b "time: $secs\n";
		print $b "bleat: $new\n";
		print $b "username: $username\n";
		close $b;

		open my $u, ">>$users_dir/$username/bleats.txt" or die "can not open $users_dir/$username/bleats.txt: $!";
		print $u "\n$epoch";
		close $u;
		$newBleatSuccess = "true";
	}
	return $newBleatSuccess;
}

sub send_bleat_button() {
	return start_form(-method=>'GET', -action=>"bitter.cgi"),
		submit({-class =>"bitter_send_button", -name=>'submit', -value=>"Send Bleat"}),
		end_form(), <p>;
}

sub login() {
    CGI->delete('svalue');
    CGI->delete('page');
	
	print start_form(-method=>'POST', -action=>"bitter.cgi");
	print "Username:\n\n";
	print "<p>";
	print textfield(-name=>'Username', -value=>"", -size=>50, -maxlength=>80, -border=>#FFFFFF, 
		-border-radius=>5);
	print "<p>";
	print "Password:\n";
	print "<p>";
	print password_field(-name=>'Password', -value=>"", -size=>50, -maxlength=>80, -border=>#FFFFFF, 
		-border-radius=>5);
	print "<p>";
	print submit({-class =>"bitter_login", -name=>'Login', -value=>"Login"});
	print end_form();
	print <p>;
}

sub searchBar() {
	return "Enter a full name or username to begin searching:\n", start_form(-method=>'GET', -action=>"bitter.cgi"),
		textfield(-name=>'svalue',
		    -value=>"",
		    -size=>50,
		    -maxlength=>80, 
			-border=>#FFFFFF,
			-border-radius=>5),
		submit({-class =>"bitter_button", -name=>'submit', -value=>"Search"}),
		end_form(),
		"<p>";
}

#sub login_button {
#    return start_form(-method=>'GET', -action=>"bitter.cgi"),
#           submit({-class =>"bitter_loginbutton", -name=>'submit', -value=>"Login"}, span({-class=>"glyphicon glyphicon-log-in"}),
#		end_form();
#}

#
# Show unformatted details for user "n".
# Increment parameter n and store it as a hidden variable
#
sub user_page {
    my $n = param('n') || 0;
    my @users = sort(glob("$users_dir/*"));
    my $user_to_show  = $users[$n % @users];
    my $details_filename = "$user_to_show/details.txt";
	my $bleats_filename = "$user_to_show/bleats.txt";
    open my $p, "$details_filename" or die "can not open $details_filename: $!";
	open my $f, "$bleats_filename" or die "can not open $bleats_filename: $!";
    @userDetails = <$p>;	
	@userBleats = <$f>;
	foreach my $line (@userDetails) {
		chomp($line);
		if ($line =~ /^username: (\w+)/) {
			my $username = $1;
			$users{$user_to_show}{user_name} = $username;
		} elsif ($line =~ /^full_name:/) {
			$line =~ s/full_name: //;
			$users{$user_to_show}{full_name} = $line;
		} elsif ($line =~ /^home_suburb:/) {
			$line =~ s/home_suburb: //;
			$users{$user_to_show}{home_suburb} = $line;
		} elsif ($line =~ /^listens:/) {
			$line =~ s/^listens: //;
			my @arr = split / /, $line;
			my $string = "";
			$string = join(" \n\t", @arr);
			$users{$user_to_show}{listens} = $string;
		}
	}
	my $user_info = "";
	$user_info = "Full Name: $users{$user_to_show}{full_name}\nUsername: $users{$user_to_show}{user_name}\nSuburb: $users{$user_to_show}{home_suburb}\nListens to:\n\t$users{$user_to_show}{listens}\n";
    close $p;
	foreach my $bleat (@userBleats) {
		open $b, "dataset-$dataset_size/bleats/$bleat" or die "can not open bleats_dir/$bleat: $!";
		my @bleatContents = <$b>;
		foreach my $bl (@bleatContents) {
			chomp($bl);
			if ($bl =~ /^time: /) {
				$bl =~ s/^time: //;
				$bleats{$bleat}{"time"} = $bl;
			} elsif ($bl =~ /^bleat: /) {
				$bl =~ s/^bleat: //;
				$bleats{$bleat}{"bleat"} = $bl;
			} 
		}
	}
	close $f;
	$bleat_info = "Displaying all bleats:";
	foreach my $key (sort { $bleats{$b}{time} <=> $bleats{$a}{time} } keys %bleats) {
		$bleat_info = join(" \n", $bleat_info, $bleats{$key}{"bleat"});
	}
    param('n', $n + 1);
    return div({-class => "bitter_user_details"}, "\n", img({-src => "$user_to_show/profile.jpg", -alt => ""}), 
		"\n$user_info\n"), div({-class => "bitter_bleats"}, "\n$bleat_info\n\n"), "\n",
        '<p>'.
        start_form, "\n",
        hidden('n'), "\n",
        submit({-class => "bitter_button", -value => 'Next user'}), "\n",
        end_form, "\n";
}


#
# HTML placed at the top of every page
#
sub page_header {
    print <<eof;
	
<!DOCTYPE html>
        <html lang="en">
        <meta charset="utf-8"> 
        <meta name="viewport" content="width=device-width, initial-scale=1"> 
       
        <head> 
        <!-- used  with permission bootstrap MIT license copyright 2015--> 
        <link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js">
            </script> 
        <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js">
            </script> 
        <link href="bitter.css" rel="stylesheet">
        <title>Bitter</title>
        <link href="bitter.css" rel="stylesheet">
        </head>
        <body>
eof
}

sub navbar {
    print <<eof;
	<nav class="navbar navbar-inverse">
		<div class="container-fluid">
			<div class="navbar-header">
				<div class="navbar-brand">
				Bitter
				</div>
			</div>
				<div>
				<ul class="nav navbar-nav">
				<li class="active"><a href="bitter.cgi?">Home</a></li>
				</ul>
				<ul class="nav navbar-nav navbar-right">
				<li><a href="bitter.cgi?submit=Login"><span class="glyphicon glyphicon-log-in"></span> Login</a></li>
				</ul>
				</div>
			</div>
		</div>
	</nav>
	<div class="bitter_global">
eof
}

sub navbar_logout {
	print <<eof;
	<nav class="navbar navbar-inverse">
		<div class="container-fluid">
			<div class="navbar-header">
				<div class="navbar-brand">
				Bitter
				</div>
			</div>
				<div>
				<ul class="nav navbar-nav">
				<li class="active"><a href="bitter.cgi?">Home</a></li>
				</ul>
				<ul class="nav navbar-nav navbar-right">
				<li><a href="bitter.cgi?submit=Logout"><span class="glyphicon glyphicon-log-out"></span> Logout</a></li>
				</ul>
				</div>
			</div>
		</div>
	</nav>
	<div class="bitter_global">
eof
}

#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
#
sub page_trailer {
	print "</div>";
    my $html = "";
    $html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
    $html .= end_html;
    return $html;
}

main();
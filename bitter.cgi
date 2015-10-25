#!/usr/bin/perl -w

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use CGI::Cookie;

sub main() {
	
	$dataset_size = "medium"; 						#initialize some variables and parameters
	$users_dir = "dataset-$dataset_size/users";
	%users = ();
	%bleats = ();
	$debug = 1;
	$submit = param('submit');
	$svalue = param('svalue');
	$svalue = lc($svalue);
	$bvalue = param('bvalue');
	$bvalue = lc($bvalue);
	$page = param('page');	
	$username = param('Username') || undef;
	$password = param('Password') || undef;
	
	my $loginSuccess = "";
	if (defined $username && defined $password) {	     #Case: When a user tries to login via the Login Page
		$loginSuccess = checkUser($username, $password); #authenticates the user and if successful, creates a cookie and sends it via header()
		CGI->delete('Username');				 	     #also prints header() regardless of success or fail
		CGI->delete('Password');
	} elsif ($submit eq "Logout") {  		     		#Case: when a user clicks on the logout link
		$loginSuccess = logout();			     		#clears all cookie values, and expires them, then sends them via header()
		CGI->delete('submit','svalue','page');
		CGI->delete('submit','svalue','page');
	} else { 				 				            #prints a header in case the previous if statements didn't execute
		print header();
	}

	# print start of HTML ASAP to assist debugging if there is an error in the script
	page_header();
	# Now tell CGI::Carp to embed any warning in HTML
	warningsToBrowser(1);
	
	%cookie = CGI::Cookie->fetch;						 #retrieves cookies to save and maintain whoever was logged in prior
	if ($cookie{'Username'} && $cookie{'Password'}) {
		$username = $cookie{'Username'}->value;
		$password = $cookie{'Password'}->value;
	} 
	
	if ((defined $username && defined $password) && !($submit eq "Logout")) {
		navbar_logout();								#prints out different navbars depending on whether
	} else { 											#a user is logged in or not
		navbar();
	}

	$newBleatSuccess = newBleat();						#function that creates a new bleat if a bleat was created via the send_bleat_page();
														#returns an empty string if it doesn't execute, false if it failed to execute.
	
	if (defined $page) {								#Functionality for the User search. Displays the User without bleats
		print searchBar();
		print bleatBar();
		print searchResult($page);
		print page_trailer();
	} elsif (($submit eq "User Search")&&(defined $svalue)) {	#Executes if a user presses the "User Search" button
		print search();
	} elsif (($submit eq "Bleat Search")&&(defined $bvalue)) {   #Executes if a user presses the "Bleat Search" button
		bleatSearch();
    } elsif ($submit eq "Login") {								#Executes if the user presses the Log In Button
        login();												#Takes them to a page where with login forms
	} elsif ($loginSuccess eq "false login") {
		param(-name=>'submit', -values=>'Login');				#Executes if the user failed to log in
		print "Invalid Username or Password\n";					#Takes them back to the login page and prints an error message
		print '<p>';
		login();
	} elsif ($submit eq "Send Bleat") {							#Executes if a user presses the "Send Bleat" button
		send_bleat_page();										#Takes them to the send bleat form
	} elsif (($newBleatSuccess eq "false")) {
		param(-name=>'submit', -values=>'Send Bleat');			#Executes if a user tries to write an invalid bleat
		print "Invalid bleat\n";								#Takes them back to the send bleat form and prints an error message
		print '<p>';
		send_bleat_page();
	} elsif ($loginSuccess eq "logout") {						#Escapes the problem of having to refresh the page for the cookie data
		print user_page();										#to be deleted.
		print page_trailer();									#Basically all the functionality of the LogOut button.
		CGI->delete('submit','svalue','page');
	} elsif ((defined $username && defined $password) || ($loginSuccess eq "login")) {
		print searchBar();
		print bleatBar();										#Basic user page when someone is logged in
		print page($username);									#Or statement is to escape the problem of 
																#having the refresh the page for cookie data to be loaded
		print page_trailer();
	} else {
		print user_page();										#Page when user is not logged in.
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

#Loads up the User Profile, send bleat button and all their Personal Bleats, 
#Listen to bleats and Bleats mentioning them
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
				$bleats{$bleat}{"bleat"} = "<tr class='bitter_tableRow2'><td class='bitter_tableRow2'> My: $bl</td></tr>";
			} 
		}
	}	
	my @listenBleats = ();
	foreach my $listen (@arr) {
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
					$bleats{$bleat}{"bleat"} = "<tr class='bitter_tableRow3'><td class='bitter_tableRow3'>$listen: $bl</td></tr>";
				}	 
			}
		}
	}
	
	my @bleat4 = sort(glob("dataset-$dataset_size/bleats/*"));
	my %temp = "";
	my $tag = "\@$page";
	my $success = "";
	foreach $bleat (@bleat4) {
		open my $t, "$bleat" or die "can not open $bleat: $!";
		my @tagBleats = <$t>;
		$success = 0;
		my $bleat_dir = "dataset-$dataset_size/bleats/";
		my $bleatID = $bleat;
		$bleatID =~ s/$bleat_dir//;
		foreach $bl (@tagBleats) {
			chomp($bl);
			if ($bl =~ /^time: /) {
				$bl =~ s/^time: //;
				$temp{"time"} = $bl;
			} elsif ($bl =~ /^bleat: /) {
				$bl =~ s/^bleat: //;
				$temp{"bleat"} = "<tr class='bitter_tableRow4'><td class='bitter_tableRow4'>tagged: $bl</td></tr>";
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
	
	$bleat_info = <<eof;
	<div class="bitter_head">
	Displaying all bleats:
	</div>
eof

	foreach my $key (sort { $bleats{$b}{time} <=> $bleats{$a}{time} } keys %bleats) {
		$bleat_info = join(" \n", $bleat_info, $bleats{$key}{"bleat"});
	}
	$allBleats = "<table class=\"table table-hover\"><tbody> $bleat_info </tbody></table>";

	print '<div class="row">'; 
    return div({-class =>"bitter_user_details col-sm-2"}, "\n", img({-src => "$user_to_show/profile.jpg", -alt => ""}), 
		"\n$user_info"), div({-class => "bitter_bleats col-sm-10"}, send_bleat_button(), "\n$allBleats\n\n"), "\n",
        '<p>', 
	print '</div>';
}

#Loads up just the User Profile. Used in conjunction with
#search() so as not to display too much info when searching
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

#Processes data and displays a table when the Bleat Search
#button is pressed
sub bleatSearch() {
	my @bleat4 = sort(glob("dataset-$dataset_size/bleats/*"));
	my %temp = "";
	my @matches = ();
	my $success = ();
	foreach my $bleat (@bleat4) {
		open my $t, "$bleat" or die "can not open $bleat: $!";
		my @tagBleats = <$t>;
		my $bleat_dir = "dataset-$dataset_size/bleats/";
		my $bleatID = $bleat;
		$bleatID =~ s/$bleat_dir//;
		foreach my $bl (@tagBleats) {
			chomp($bl);
			$bl = lc($bl);
			if ($bl =~ /^bleat: /) {
				$bl =~ s/^bleat: //;
				if ($bl =~ /$bvalue/) {
					push (@matches, $bl);
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

	if ($#matches == "-1") {
		print "Your search returned 0 matches";
		print '<p>';
		print bleatBar(); 
		print page_trailer();
	} else {
		my $string = "";
		foreach my $match (@matches) {
            $string .= <<eof;
            <tr class="bitter_tableRow"><td class="bitter_tableRow">        
            $match        
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
		print bleatBar();
		print $toReturn;
		print page_trailer();
	}
}

#Displays the bleat search bar
sub bleatBar() {
	return start_form(-method=>'GET', -action=>"bitter.cgi"),
		textfield(-name=>'bvalue',
		    -value=>"",
		    -size=>50,
		    -maxlength=>80, 
			-border=>#FFFFFF,
			-border-radius=>5),
		submit({-class =>"bitter_bleat_button", -name=>'submit', -value=>"Bleat Search"}),
		end_form(),
		"<p>";
}

#Processes data and displays a table when the User Search
#button is pressed
sub search() {
	my @users = sort(glob("$users_dir/*"));
	my $success = 0;
	my @matches = ();
	foreach my $file (@users) {
		my $details_filename = "$file/details.txt";
		open my $p, "$details_filename" or die "can not open $details_filename: $!";
		@details = <$p>;
		foreach my $line (@details) {
			chomp($line);
			$line = lc($line);
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

#Authenticates the User if they tried to log in
#Creates a cookie if successful.
#Always prints header().
#Returns login if successful, false login if not
sub checkUser() {
	my ($name, $password) = @_;
	my $success = 0;
    my $details_filename = "$users_dir/$name/details.txt";
	open my $p, "$details_filename" or $success = "fail";
	@userDetails = <$p>;
	if (!($success eq "fail")) {
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
	} else {
		print header();
		$success = "false login";
		return $success;
	}
}

#Loads up the page where users send bleats
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

#Processes data and creates a bleat when
#a new bleat is made (via send_bleat_page)
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

#Displays the send bleat button
sub send_bleat_button() {
	return start_form(-method=>'GET', -action=>"bitter.cgi"),
		submit({-class =>"bitter_send_button", -name=>'submit', -value=>"Send Bleat"}),
		end_form(), <p>;
}

#Loads up the page where users try to login
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

#Displays the User Search Bar
sub searchBar() {
	return "Enter a full name or username to begin searching:\n", start_form(-method=>'GET', -action=>"bitter.cgi"),
		textfield(-name=>'svalue',
		    -value=>"",
		    -size=>50,
		    -maxlength=>80, 
			-border=>#FFFFFF,
			-border-radius=>5),
		submit({-class =>"bitter_button", -name=>'submit', -value=>"User Search"}),
		end_form();
}

#Basic page when user is not logged in
#Show unformatted details for user "n".
#Increment parameter n and store it as a hidden variable
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

#Navbar when not logged in
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

#Navbar when user is logged in
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

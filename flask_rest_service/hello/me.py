my_dict = {'10.38.0.1' : 'HostA', '10.38.0.2' : 'HostB', '10.38.1.0' : 'HostC', '10.38.1.1' : 'HostD', '10.38.3.0' : 'HostE'}
my_list = ['10.38.0.1', '10.38.0.2', '10.38.1.0', '10.38.1.1', '10.38.3.0']



def to_create_file():
    subnet_dict = {}
    for i in my_list:
        subnet_key = subnet_dict.keys()
        ip_third_octate = i.split('.')[0:3]
        ip_third_octate='.'.join(ip_third_octate)
      
        if not ip_third_octate in subnet_key:
            subnet_dict[ip_third_octate]=[i]
        else:
            previous_ips = subnet_dict[ip_third_octate]
            subnet_dict[ip_third_octate]=[i, *previous_ips]

    for key, value in subnet_dict.items():
       print(f"hello this is title:{key}")
       for i in value:
           print(f"{i}   HOST NAME:{my_dict[i]}")

to_create_file()
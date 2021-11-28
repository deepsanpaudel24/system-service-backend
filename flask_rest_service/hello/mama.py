my_dict = {'10.38.0.1' : 'HostA', '10.38.0.2' : 'HostB', '10.38.1.0' : 'HostC', '10.38.1.1' : 'HostD', '10.38.3.0' : 'HostE'}
my_list = ['10.38.0.1', '10.38.0.2', '10.38.1.0', '10.38.1.1', '10.38.3.0']
def to_create_file():
    for i in my_list:
        curr_ip = i
        print(i, "this is ip")
        nxt_ip = my_list[my_list.index(i) + 1]
        print(nxt_ip, "this is nxt ip")

        curr_third_split = curr_ip.split('.')
        print(curr_third_split, "this is curr_third_split")

        curr_third_octet = curr_third_split[2]

        nxt_third_split = nxt_ip.split('.')
        nxt_third_octet = nxt_third_split[2]

        print(my_dict.items(), "hello world")

        

        for k, v in my_dict.items():
            if i in k:
                print(i, v)
                if nxt_third_octet == curr_third_octet:
                    # file.write(reverse_zone_data + "\n")
                    break
                else:
                    new_line = ('\n')
                    print(new_line)
                    #file.write(new_line + "\n")

to_create_file()
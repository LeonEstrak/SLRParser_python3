grammars = open("grammar.txt")
parsed_Grammar = {}
collection_of_items = {}
start = ""
terminals = []
nonterminals = []
symbols = []

def parse_grammar():
    global parsed_Grammar, start, terminals, nonterminals, symbols
    for line in grammars:
        line = " ".join(line.split())
        if line == '\n':
            break
        head = line[:line.index("->")].strip()
        prods = [l.strip().split(' ') for l in ''.join(line[line.index("->") + 2:]).split('|')]
        if not start:
            start = head + "'"
            parsed_Grammar[start] = [[head]]
            nonterminals.append(start)
        if head not in parsed_Grammar:
            parsed_Grammar[head] = []
        if head not in nonterminals:
            nonterminals.append(head)
        for prod in prods:
            parsed_Grammar[head].append(prod)
            for char in prod:
                if not char.isupper() and char not in terminals:
                    terminals.append(char)
                elif char.isupper() and char not in nonterminals:
                    nonterminals.append(char)
                    parsed_Grammar[char] = []    #non terminals dont produce other symbols
    symbols =  nonterminals+terminals
first_seen = []

def FIRST(X):
    global first_seen
    first = []
    first_seen.append(X)
    if X in terminals:  # CASE 1
        first.append(X)
    elif X in nonterminals:
        for prods in parsed_Grammar[X]:  # CASE 2
            if prods[0] in terminals and prods[0] not in first:
                first.append(prods[0])
            else:  # CASE 3
                for nonterm in prods:
                    if nonterm not in first_seen:
                        for terms in FIRST(nonterm):
                            if terms not in first:
                                first.append(terms)
    first_seen.remove(X)
    return first


follow_seen = []
def FOLLOW(A):
    global follow_seen
    follow = []
    follow_seen.append(A)
    if A == start:  # CASE 1
        follow.append('$')
    for heads in list(parsed_Grammar.keys()):
        for prods in parsed_Grammar[heads]:
            follow_head = False
            if A in prods:
                next_symbol_pos = prods.index(A) + 1
                if next_symbol_pos < len(prods):  # CASE 2
                    for terms in FIRST(prods[next_symbol_pos]):
                        if terms not in follow:
                            follow.append(terms)
                else:  # CASE 3
                    follow_head = True
                if follow_head and heads not in follow_seen:
                    for terms in FOLLOW(heads):
                        if terms not in follow:
                            follow.append(terms)
    follow_seen.remove(A)
    return follow

def closure(I):
    J = I
    while True:
        item_len = len(J) + sum(len(v) for v in J.values())
        for heads in list(J.keys()):
            for prods in J[heads]:
                dot_pos = prods.index('.')      #checks if final item or not
                if dot_pos + 1 < len(prods):
                    prod_after_dot = prods[dot_pos + 1]
                    if prod_after_dot in nonterminals:
                        for prod in parsed_Grammar[prod_after_dot]:                   
                            item = ["."] + prod
                            if prod_after_dot not in list(J.keys()):
                                J[prod_after_dot] = [item]
                            elif item not in J[prod_after_dot]:
                                J[prod_after_dot].append(item)
        if item_len == len(J) + sum(len(v) for v in J.values()):
            return J

def GOTO(I, X):
    goto = {}
    for heads in list(I.keys()):
        for prods in I[heads]:
            for i in range(len(prods) - 1):
                if "." == prods[i] and X == prods[i + 1]:
                    temp_prods = prods[:]
                    temp_prods[i], temp_prods[i + 1] = temp_prods[i + 1], temp_prods[i]
                    prod_closure = closure({heads: [temp_prods]})
                    for keys in prod_closure:
                        if keys not in list(goto.keys()):
                            goto[keys] = prod_closure[keys]
                        elif prod_closure[keys] not in goto[keys]:
                            for prod in prod_closure[keys]:
                                goto[keys].append(prod)
    return goto

def items():
    global collection_of_items
    i = 1
    collection_of_items = {'I0': closure({start: [['.'] + parsed_Grammar[start][0]]})}
    while True:
        item_len = len(collection_of_items) + sum(len(v) for v in collection_of_items.values())
        for I in list(collection_of_items.keys()):
            for X in symbols:
                if GOTO(collection_of_items[I], X) and GOTO(collection_of_items[I], X) not in list(collection_of_items.values()):
                    collection_of_items['I' + str(i)] = GOTO(collection_of_items[I], X)
                    i += 1
        if item_len == len(collection_of_items) + sum(len(v) for v in collection_of_items.values()):
            return


def ACTION(i, a):
    for heads in collection_of_items['I' + str(i)]:
        for prods in collection_of_items['I' + str(i)][heads]:
            for j in range(len(prods) - 1):
                if prods[j] == '.' and prods[j + 1] == a:
                    for k in range(len(collection_of_items)):
                        if GOTO(collection_of_items['I' + str(i)], a) == collection_of_items['I' + str(k)]:
                            if a in terminals:
                                if "r" in parse_table[i][terminals.index(a)]:
                                    # if error%2==0:
                                    #     print("ERROR: Shift-Reduce Conflict at State " + str(i) + ", Symbol \'" + str(terminals.index(a))+"\'")
                                    # error+=1
                                    if "s"+str(k) not in parse_table[i][terminals.index(a)]:
                                        parse_table[i][terminals.index(a)] = parse_table[i][terminals.index(a)]+ "/s" + str(k)
                                    return parse_table[i][terminals.index(a)]
                                else:
                                    parse_table[i][terminals.index(a)] = "s" + str(k)
                            else:
                                parse_table[i][len(terminals) + nonterminals.index(a)] = str(k)
                            return "s" + str(k)
    for heads in collection_of_items['I' + str(i)]:
        if heads != start:
            for prods in collection_of_items['I' + str(i)][heads]:
                if prods[-1] == '.':             #final item 
                    k = 0
                    for head in list(parsed_Grammar.keys()):
                        for Gprods in parsed_Grammar[head]:
                            if head == heads and (Gprods == prods[:-1] ) and (a in terminals or a == '$'):
                                for terms in FOLLOW(heads):
                                    if terms == '$':
                                        index = len(terminals)
                                    else:
                                        index = terminals.index(terms)
                                    if "s" in parse_table[i][index]:
                                        # if error%2==0:
                                        #     print("ERROR: Shift-Reduce Conflict at State " + str(i) + ", Symbol \'" + str(terms)+"\'")
                                        # error+=1
                                        if "r"+str(k) not in parse_table[i][index]:
                                            parse_table[i][index] = parse_table[i][index]+ "/r" + str(k)
                                        return parse_table[i][index]
                                    elif parse_table[i][index] and parse_table[i][index] != "r" + str(k):
                                        # if error%2==0:
                                        #     print("ERROR: Reduce-Reduce Conflict at State " + str(i) + ", Symbol \'" + str(terms)+"\'")
                                        # error+=1
                                        if "r"+str(k) not in parse_table[i][index]:
                                                parse_table[i][index] = parse_table[i][index]+ "/r" + str(k)
                                        return parse_table[i][index]                                
                                    else:
                                        parse_table[i][index] = "r" + str(k)
                                return "r" + str(k)
                            k += 1
    if start in collection_of_items['I' + str(i)] and parsed_Grammar[start][0] + ['.'] in collection_of_items['I' + str(i)][start]:
        parse_table[i][len(terminals)] = "acc"
        return "acc"
    return ""

def print_info():
    print("GRAMMAR:")
    for head in list(parsed_Grammar.keys()):
        if head == start:
            continue
        print("{:>{width}} ->".format(head, width=len(max(list(parsed_Grammar.keys()), key=len))), end=' ')
        num_prods = 0
        for prods in parsed_Grammar[head]:
            if num_prods > 0:
                print("|", end=' ')
            for prod in prods:
                print(prod, end=' ')
            num_prods += 1
        print()
    print("\nAUGMENTED GRAMMAR:")
    i = 0
    for head in list(parsed_Grammar.keys()):
        for prods in parsed_Grammar[head]:
            print("{:>{width}}:".format(str(i), width=len(str(sum(len(v) for v in parsed_Grammar.values()) - 1))), end=' ')
            print("{:>{width}} ->".format(head, width=len(max(list(parsed_Grammar.keys()), key=len))), end=' ')
            for prod in prods:
                print(prod, end=' ')
            print()
            i += 1
    print("\nTERMINALS   :", terminals)
    print("NONTERMINALS:", nonterminals)
    print("SYMBOLS     :", symbols)
    print("\nFIRST:")
    for head in parsed_Grammar:
        print("{:>{width}} =".format(head, width=len(max(list(parsed_Grammar.keys()), key=len))), end=' ')
        print("{", end=' ')
        num_terms = 0
        for terms in FIRST(head):
            if num_terms > 0:
                print(", ", end=' ')
            print(terms, end=' ')
            num_terms += 1
        print("}")

    print("\nFOLLOW:")
    for head in parsed_Grammar:
        print("{:>{width}} =".format(head, width=len(max(list(parsed_Grammar.keys()), key=len))), end=' ')
        print("{", end=' ')
        num_terms = 0
        for terms in FOLLOW(head):
            if num_terms > 0:
                print(", ", end=' ')
            print(terms, end=' ')
            num_terms += 1
        print("}")

    print("\nITEMS:")
    for i in range(len(collection_of_items)):
        print('I' + str(i) + ':')
        for keys in collection_of_items['I' + str(i)]:
            for prods in collection_of_items['I' + str(i)][keys]:
                print("{:>{width}} ->".format(keys, width=len(max(list(parsed_Grammar.keys()), key=len))), end=' ')
                for prod in prods:
                    print(prod, end=' ')
                print()
        print()

    for i in range(len(parse_table)):       #len gives number of states
        for j in symbols:
            ACTION(i, j)

    print("PARSING TABLE:")
    print("+" + "--------+" * (len(terminals) + len(nonterminals) + 1))
    print("|{:^8}|".format('STATE'), end=' ')
    for terms in terminals:
        print("{:^7}|".format(terms), end=' ')
    print("{:^7}|".format("$"), end=' ')
    for nonterms in nonterminals:
        if nonterms == start:
            continue
        print("{:^7}|".format(nonterms), end=' ')
    print("\n+" + "--------+" * (len(terminals) + len(nonterminals) + 1))
    for i in range(len(parse_table)):
        print("|{:^8}|".format(i), end=' ')
        for j in range(len(parse_table[i]) - 1):
            print("{:^7}|".format(parse_table[i][j]), end=' ')
        print()
    print("+" + "--------+" * (len(terminals) + len(nonterminals) + 1))

def process_input():
    get_input = input("\nEnter Input String: ")
    to_parse = " ".join((get_input + " $").split()).split(" ")
    pointer = 0
    stack = ['0']

    print("\n+--------+----------------------------+----------------------------+----------------------------+")
    print("|{:^8}|{:^28}|{:^28}|{:^28}|".format("STEP", "STACK", "INPUT", "ACTION"))
    print("+--------+----------------------------+----------------------------+----------------------------+")

    step = 1
    while True:
        curr_symbol = to_parse[pointer]
        top_stack = int(stack[-1])
        stack_content = ""
        input_content = ""

        print("|{:^8}|".format(step), end=' ')
        for i in stack:
            stack_content += i
        print("{:27}|".format(stack_content), end=' ')
        i = pointer
        while i < len(to_parse):
            input_content += to_parse[i]
            i += 1
        print("{:>26} | ".format(input_content), end=' ')

        step += 1
        get_action = ACTION(top_stack, curr_symbol)
        if "/" in get_action:
            print("{:^26}|".format(get_action+". So conflict"))
            break
        if "s" in get_action:
            print("{:^26}|".format(get_action))
            stack.append(curr_symbol)
            stack.append(get_action[1:])
            pointer += 1
        elif "r" in get_action:
            print("{:^26}|".format(get_action))
            i = 0
            for head in list(parsed_Grammar.keys()):
                for prods in parsed_Grammar[head]:
                    if i == int(get_action[1:]):
                        for j in range(2 * len(prods)):
                            stack.pop()
                        state = stack[-1]
                        stack.append(head)
                        stack.append(parse_table[int(state)][len(terminals) + nonterminals.index(head)])
                    i += 1
        elif get_action == "acc":
            print("{:^26}|".format("ACCEPTED"))
            break
        else:
            print("\tERROR:Invalid String\t|")
            break
    print("+--------+----------------------------+----------------------------+----------------------------+")

if __name__ == '__main__':
    parse_grammar()
    items()
    parse_table = [["" for c in range(len(terminals) + len(nonterminals) + 1)] for r in range(len(collection_of_items))]
    print_info()
    while True:
        process_input()
        choice = input("\n\nDo you want to enter another string ?[Y/n]")
        if(choice.strip() == "n"):
            break
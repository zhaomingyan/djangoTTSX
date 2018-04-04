def get_page_list(total_page,pindex):
    # 构造页码列表，用于提示页码链接
    page_list = []  # 3 4 5 6 7==> range(n-2,n+3)
    # 如果不足5页，显示所有数字
    if total_page <= 5:
        page_list = range(1, total_page + 1)
    elif pindex <= 2:  # 如果是1到2页，则显示1-5
        page_list = range(1, 6)
    elif pindex > total_page - 1:  # 如果是后两页，则显示最后5页
        page_list = range(total_page - 4, total_page + 1)  # 共18页，则最后的数字是14 15 16 17 18
    else:
        page_list = range(pindex - 2, pindex + 3)

    return page_list
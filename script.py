import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

class JsonManagerApp:
    def __init__(self, master, filename):
        self.master = master
        self.filename = os.path.abspath(filename)
        self.data = []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.master.title("美食地图数据管理")
        self.master.geometry("1200x720")
        self.master.configure(bg="#f0f0f0")

        # 主框架
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 15))

        # 按钮样式
        button_style = ttk.Style()
        button_style.configure("TButton", padding=6, font=('微软雅黑', 10))

        ttk.Button(toolbar, text="＋ 添加", command=self.add_item).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="✎ 修改", command=self.edit_item).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="✖ 删除", command=self.delete_item).pack(side=tk.LEFT, padx=3)

        # 表格列定义
        columns = {
            "name": ("店铺名称", 180),
            "cuisine": ("菜系", 120),
            "address": ("详细地址", 250),
            "dishes": ("推荐菜品", 200),
            "recommendation": ("推荐理由", 300),
            "latitude": ("纬度", 120),
            "longitude": ("经度", 120),
            "updated": ("更新时间", 180)
        }

        # 创建表格
        self.tree = ttk.Treeview(
            main_frame,
            columns=list(columns.keys()),
            show="headings",
            selectmode="browse",
            style="Custom.Treeview"
        )

        # 表格样式
        tree_style = ttk.Style()
        tree_style.configure("Custom.Treeview", font=('微软雅黑', 10), rowheight=30)
        tree_style.configure("Custom.Treeview.Heading",
                           font=('微软雅黑', 11, 'bold'),
                           background="#ea945a",
                           foreground="white")

        # 设置列
        for col, (text, width) in columns.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.W)

        # 滚动条
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def load_data(self):
        try:
            # 自动创建文件
            if not os.path.exists(self.filename):
                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump([], f)

            with open(self.filename, 'r', encoding='utf-8') as f:
                old_data = json.load(f)

            self.data = []
            for item in old_data:
                new_item = {
                    "name": item.get("name", "未命名店铺"),
                    "address": item.get("address", "地址未填写"),
                    "dishes": item.get("dishes", "暂无推荐菜品"),
                    "cuisine": item.get("cuisine", "暂无分类"),
                    "recommendation": item.get("recommendation", "暂无推荐理由"),
                    "latitude": float(item.get("latitude", 0.0)),
                    "longitude": float(item.get("longitude", 0.0)),
                    "updated": item.get("updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                }
                self.data.append(new_item)
            self.save_data()  # 转换旧数据格式
            self.update_treeview()
        except Exception as e:
            messagebox.showerror("错误", f"数据加载失败: {str(e)}")

    def save_data(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}\n请检查文件是否被占用或权限不足")
            return False

    def update_treeview(self):
        self.tree.delete(*self.tree.get_children())
        for item in self.data:
            self.tree.insert("", "end", values=(
                item["name"],
                item["cuisine"],
                item["address"],
                item["dishes"],
                item["recommendation"],
                f"{item['latitude']:.6f}",
                f"{item['longitude']:.6f}",
                item["updated"]
            ))

    def add_item(self):
        dialog = AddEditDialog(self.master, "添加新店铺")
        if dialog.result:
            self.data.append(dialog.values)
            if self.save_data():
                self.update_treeview()

    def edit_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的条目")
            return

        index = self.tree.index(selected[0])
        dialog = AddEditDialog(
            self.master,
            "修改店铺信息",
            **self.data[index]
        )
        if dialog.result:
            self.data[index] = dialog.values
            if self.save_data():
                self.update_treeview()

    def delete_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的条目")
            return

        if messagebox.askyesno("确认", "确定删除该条目吗？"):
            index = self.tree.index(selected[0])
            del self.data[index]
            if self.save_data():
                self.update_treeview()


class AddEditDialog(simpledialog.Dialog):
    def __init__(self, parent, title, **kwargs):
        self.values = {}
        self.result = False
        self.inputs = {
            "name": kwargs.get("name", ""),
            "address": kwargs.get("address", ""),
            "dishes": kwargs.get("dishes", ""),
            "cuisine": kwargs.get("cuisine", ""),
            "recommendation": kwargs.get("recommendation", ""),
            "latitude": kwargs.get("latitude", ""),
            "longitude": kwargs.get("longitude", "")
        }
        super().__init__(parent, title)

    def body(self, frame):
        entries = [
            ("店铺名称", "name", 0),
            ("详细地址", "address", 1),
            ("推荐菜品", "dishes", 2),
            ("菜系", "cuisine", 3),
            ("推荐理由", "recommendation", 4),
            ("纬度", "latitude", 5),
            ("经度", "longitude", 6)
        ]
        for text, key, row in entries:
            ttk.Label(frame, text=f"{text}：", font=('微软雅黑', 10)).grid(row=row, column=0, sticky=tk.E, pady=6)
            entry = ttk.Entry(frame, width=35, font=('微软雅黑', 10))
            entry.grid(row=row, column=1, padx=10, pady=6, sticky=tk.W)
            entry.insert(0, str(self.inputs[key]))
            setattr(self, f"{key}_entry", entry)
        return frame

    def validate(self):
        try:
            self.values = {
                "name": self.name_entry.get().strip(),
                "address": self.address_entry.get().strip(),
                "dishes": self.dishes_entry.get().strip(),
                "cuisine": self.cuisine_entry.get().strip(),
                "recommendation": self.recommendation_entry.get().strip(),
                "latitude": float(self.latitude_entry.get()),
                "longitude": float(self.longitude_entry.get()),
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.values["name"]:
                messagebox.showwarning("警告", "店铺名称不能为空")
                return False
            if len(self.values["recommendation"]) > 100:
                messagebox.showwarning("警告", "推荐理由不能超过100字")
                return False
            return True
        except ValueError:
            messagebox.showwarning("错误", "经纬度必须为数字")
            return False

    def apply(self):
        self.result = True


if __name__ == "__main__":
    root = tk.Tk()
    root.style = ttk.Style()
    root.style.theme_use("clam")
    root.option_add("*Font", "微软雅黑 10")
    app = JsonManagerApp(root, "data-shops.json")
    root.mainloop()
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime


class JsonManagerApp:
    def __init__(self, master, filename):
        self.master = master
        self.filename = filename
        self.data = []

        # 初始化界面
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """设置界面布局"""
        self.master.title("美食地图数据管理")
        self.master.geometry("1200x720")
        self.master.configure(bg="#f0f0f0")

        # 主框架
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 15))

        button_style = ttk.Style()
        button_style.configure("TButton", padding=6, font=('微软雅黑', 10))

        ttk.Button(toolbar, text="＋ 添加", command=self.add_item, style="TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="✎ 修改", command=self.edit_item, style="TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="✖ 删除", command=self.delete_item, style="TButton").pack(side=tk.LEFT, padx=3)

        # 数据表格
        columns = {
            "name": ("店铺名称", 180),
            "address": ("详细地址", 250),
            "dishes": ("推荐菜品", 200),
            "latitude": ("纬度", 120),
            "longitude": ("经度", 120),
            "updated": ("更新时间", 180)
        }

        self.tree = ttk.Treeview(
            main_frame,
            columns=list(columns.keys()),
            show="headings",
            selectmode="browse",
            style="Custom.Treeview"
        )

        # 自定义样式
        tree_style = ttk.Style()
        tree_style.configure("Custom.Treeview",
                             font=('微软雅黑', 10),
                             rowheight=30,
                             bordercolor="#e0e0e0")
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
        """加载并转换旧格式数据"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                old_data = json.load(f)

            # 数据格式转换
            self.data = []
            for item in old_data:
                new_item = {
                    "name": item.get("name", ""),
                    "latitude": item.get("latlng", [0, 0])[0],
                    "longitude": item.get("latlng", [0, 0])[1],
                    "address": item.get("info", "").split("<br>")[0].replace("📍 ", ""),
                    "dishes": item.get("info", "").split("<br>")[1] if "<br>" in item.get("info", "") else "",
                    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.data.append(new_item)

            self.save_data()  # 保存新格式
            self.update_treeview()

        except FileNotFoundError:
            self.data = []
        except Exception as e:
            messagebox.showerror("错误", f"数据加载失败: {str(e)}")

    def save_data(self):
        """保存数据到JSON文件"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
            return False

    def update_treeview(self):
        """更新表格显示"""
        self.tree.delete(*self.tree.get_children())
        for item in self.data:
            self.tree.insert("", "end", values=(
                item["name"],
                item["address"],
                item["dishes"],
                f"{item['latitude']:.6f}",
                f"{item['longitude']:.6f}",
                item["updated"]
            ))

    def add_item(self):
        """添加新条目"""
        dialog = AddEditDialog(self.master, "添加新店铺")
        if dialog.result:
            new_item = {
                "name": dialog.values["name"],
                "address": dialog.values["address"],
                "dishes": dialog.values["dishes"],
                "latitude": dialog.values["latitude"],
                "longitude": dialog.values["longitude"],
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.data.append(new_item)
            if self.save_data():
                self.update_treeview()

    def edit_item(self):
        """修改选中条目"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的条目")
            return

        index = self.tree.index(selected[0])
        original = self.data[index]

        dialog = AddEditDialog(
            self.master,
            "修改店铺信息",
            name=original["name"],
            address=original["address"],
            dishes=original["dishes"],
            latitude=original["latitude"],
            longitude=original["longitude"]
        )

        if dialog.result:
            self.data[index] = {
                "name": dialog.values["name"],
                "address": dialog.values["address"],
                "dishes": dialog.values["dishes"],
                "latitude": dialog.values["latitude"],
                "longitude": dialog.values["longitude"],
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if self.save_data():
                self.update_treeview()

    def delete_item(self):
        """删除选中条目"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的条目")
            return

        if messagebox.askyesno("确认", "确定要删除选中的条目吗？"):
            index = self.tree.index(selected[0])
            del self.data[index]
            if self.save_data():
                self.update_treeview()


class AddEditDialog(simpledialog.Dialog):
    """添加/修改条目对话框"""

    def __init__(self, parent, title, name="", address="", dishes="", latitude="", longitude=""):
        self.values = {}
        self.result = False
        self.inputs = {
            "name": name,
            "address": address,
            "dishes": dishes,
            "latitude": latitude,
            "longitude": longitude
        }
        super().__init__(parent, title)

    def body(self, frame):
        """创建对话框内容"""
        self.configure(background="#f8f9fa")
        frame.config(padx=15, pady=15)

        # 店铺名称
        ttk.Label(frame, text="店铺名称：", font=('微软雅黑', 10)).grid(row=0, column=0, sticky=tk.E, pady=6)
        self.name_entry = ttk.Entry(frame, width=35, font=('微软雅黑', 10))
        self.name_entry.grid(row=0, column=1, padx=10, pady=6, sticky=tk.W)
        self.name_entry.insert(0, self.inputs["name"])

        # 详细地址
        ttk.Label(frame, text="详细地址：", font=('微软雅黑', 10)).grid(row=1, column=0, sticky=tk.E, pady=6)
        self.address_entry = ttk.Entry(frame, width=35, font=('微软雅黑', 10))
        self.address_entry.grid(row=1, column=1, padx=10, pady=6, sticky=tk.W)
        self.address_entry.insert(0, self.inputs["address"])

        # 推荐菜品
        ttk.Label(frame, text="推荐菜品：", font=('微软雅黑', 10)).grid(row=2, column=0, sticky=tk.E, pady=6)
        self.dishes_entry = ttk.Entry(frame, width=35, font=('微软雅黑', 10))
        self.dishes_entry.grid(row=2, column=1, padx=10, pady=6, sticky=tk.W)
        self.dishes_entry.insert(0, self.inputs["dishes"])

        # 经纬度
        ttk.Label(frame, text="纬度：", font=('微软雅黑', 10)).grid(row=3, column=0, sticky=tk.E, pady=6)
        self.lat_entry = ttk.Entry(frame, width=15, font=('微软雅黑', 10))
        self.lat_entry.grid(row=3, column=1, padx=10, pady=6, sticky=tk.W)
        self.lat_entry.insert(0, self.inputs["latitude"])

        ttk.Label(frame, text="经度：", font=('微软雅黑', 10)).grid(row=4, column=0, sticky=tk.E, pady=6)
        self.lng_entry = ttk.Entry(frame, width=15, font=('微软雅黑', 10))
        self.lng_entry.grid(row=4, column=1, padx=10, pady=6, sticky=tk.W)
        self.lng_entry.insert(0, self.inputs["longitude"])

        return frame

    def validate(self):
        """验证输入"""
        try:
            self.values = {
                "name": self.name_entry.get().strip(),
                "address": self.address_entry.get().strip(),
                "dishes": self.dishes_entry.get().strip(),
                "latitude": float(self.lat_entry.get()),
                "longitude": float(self.lng_entry.get())
            }

            if not self.values["name"]:
                messagebox.showwarning("警告", "店铺名称不能为空")
                return False

            if not (-90 <= self.values["latitude"] <= 90):
                messagebox.showwarning("警告", "纬度范围应为-90到90")
                return False

            if not (-180 <= self.values["longitude"] <= 180):
                messagebox.showwarning("警告", "经度范围应为-180到180")
                return False

            return True
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的经纬度数值")
            return False

    def apply(self):
        self.result = True


if __name__ == "__main__":
    root = tk.Tk()
    root.style = ttk.Style()
    root.style.theme_use("clam")

    # 设置全局字体
    root.option_add("*Font", "微软雅黑 10")

    app = JsonManagerApp(root, "data-shops.json")
    root.mainloop()
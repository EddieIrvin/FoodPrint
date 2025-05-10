import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime


class JsonManagerApp:
    def __init__(self, master, filename):
        self.master = master
        self.data_dir = os.path.join(os.path.dirname(__file__), "database")
        self.filename = os.path.join(self.data_dir, filename)
        os.makedirs(self.data_dir, exist_ok=True)

        self.data = []
        self.setup_ui()
        self.load_data()
        self.selected_index = None

    def setup_ui(self):
        """初始化用户界面"""
        self.master.title("美食地图数据管理")
        self.master.geometry("1280x720")  # 固定初始尺寸

        # 主容器（左右分割比例4:1）
        main_paned = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # ========== 左侧表格区域 ==========
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=4)

        # 工具栏
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=tk.X, pady=(10, 5), padx=10)

        ttk.Button(toolbar, text="＋ 添加", command=self.add_item, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✎ 修改", command=self.edit_item, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✖ 删除", command=self.delete_item, width=8).pack(side=tk.LEFT, padx=2)

        # 搜索框
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT)
        ttk.Label(search_frame, text="搜索：").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_data())

        # 数据表格
        columns = {
            "name": ("店铺名称", 220),
            "cuisine": ("菜系", 100),
            "dishes": ("推荐菜品", 280),
            "updated": ("更新时间", 180)
        }
        self.tree = ttk.Treeview(
            left_frame,
            columns=list(columns.keys()),
            show="headings",
            selectmode="browse",
            style="Custom.Treeview"
        )
        for col, (text, width) in columns.items():
            self.tree.heading(col, text=text, anchor=tk.W)
            self.tree.column(col, width=width, minwidth=80, anchor=tk.W)

        vsb = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # ========== 右侧预览区域 ==========
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)

        # 预览标题
        ttk.Label(right_frame, text="详细信息", font=('微软雅黑', 12),
                  foreground="#2c3e50").pack(pady=10)

        # 预览内容容器
        preview_container = ttk.Frame(right_frame)
        preview_container.pack(fill=tk.BOTH, expand=True, padx=10)

        # 信息展示字段
        self.preview_fields = [
            ("店铺名称", "name", 80),
            ("菜系", "cuisine", 80),
            ("地址", "address", 120),
            ("推荐菜品", "dishes", 120),
            ("推荐理由", "recommendation", 120),
            ("经纬度", "coordinates", 80),
            ("更新时间", "updated", 80)
        ]

        self.preview_labels = {}
        for idx, (text, key, height) in enumerate(self.preview_fields):
            row = ttk.Frame(preview_container)
            row.grid(row=idx, column=0, sticky="ew", pady=2)

            ttk.Label(row, text=f"{text}：", width=8, anchor=tk.E).pack(side=tk.LEFT)

            if key in ["address", "dishes", "recommendation"]:
                entry = tk.Text(row, width=24, height=height // 20, wrap=tk.WORD,
                                font=('微软雅黑', 9), relief="flat", bg="#f8f9fa")
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                entry = ttk.Label(row, text="", font=('微软雅黑', 9),
                                  background="#f8f9fa", width=24)
                entry.pack(side=tk.LEFT)

            self.preview_labels[key] = entry

        # 状态栏
        self.status_bar = ttk.Label(self.master, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.configure_styles()

    def configure_styles(self):
        """统一样式配置"""
        style = ttk.Style()
        style.theme_use("clam")

        # 增强选中行对比度
        style.configure("Custom.Treeview",
                        font=('微软雅黑', 10),
                        rowheight=28,
                        fieldbackground="#ffffff",
                        borderwidth=0)
        style.map("Custom.Treeview",
                  background=[("selected", "#cce5ff")])  # 高对比度选中色

        style.configure("Custom.Treeview.Heading",
                        font=('微软雅黑', 10, 'bold'),
                        background="#3a3f45",
                        foreground="white",
                        padding=6)

    def update_preview(self):
        """更新预览内容"""
        if self.selected_index is None:
            return

        item = self.data[self.selected_index]
        # 修正后的菜品显示（无•符号）
        dishes = "\n".join([d.strip() for d in item["dishes"].split(",")])

        self.preview_labels["name"].configure(text=item["name"][:20])
        self.preview_labels["cuisine"].configure(text=item["cuisine"][:15])

        self.preview_labels["address"].delete("1.0", tk.END)
        self.preview_labels["address"].insert(tk.END, item.get("address", ""))

        self.preview_labels["dishes"].delete("1.0", tk.END)
        self.preview_labels["dishes"].insert(tk.END, dishes)

        self.preview_labels["recommendation"].delete("1.0", tk.END)
        self.preview_labels["recommendation"].insert(tk.END, item.get("recommendation", ""))

        self.preview_labels["coordinates"].configure(
            text=f"{item['latitude']:.4f}, {item['longitude']:.4f}")
        self.preview_labels["updated"].configure(text=item["updated"][:19])

    def filter_data(self):
        """搜索过滤功能"""
        keyword = self.search_var.get().lower()
        filtered = [
            item for item in self.data
            if keyword in item["name"].lower() or
               keyword in item["cuisine"].lower() or
               keyword in item["dishes"].lower()
        ]
        self.tree.delete(*self.tree.get_children())
        for item in filtered:
            self.tree.insert("", "end", values=(
                item["name"],
                item["cuisine"],
                item["dishes"],
                item["updated"]
            ))

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_index = self.tree.index(selected[0])
        self.update_preview()
        self.status_bar.config(text=f"已选择：{self.data[self.selected_index]['name']}")

    def load_data(self):
        """加载数据文件"""
        try:
            if not os.path.exists(self.filename):
                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump([], f)

            with open(self.filename, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            self.data = []
            for item in raw_data:
                processed_item = {
                    "name": item.get("name", "未命名店铺"),
                    "address": item.get("address", "地址未填写"),
                    "dishes": item.get("dishes", "暂无推荐菜品"),
                    "cuisine": item.get("cuisine", "暂无分类"),
                    "recommendation": item.get("recommendation", "暂无推荐理由"),
                    "latitude": float(item.get("latitude", 0.0)),
                    "longitude": float(item.get("longitude", 0.0)),
                    "updated": item.get("updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                }
                self.data.append(processed_item)

            self.save_data()
            self.update_treeview()

        except Exception as e:
            messagebox.showerror("加载错误", f"数据加载失败: {str(e)}")

    def save_data(self):
        """保存数据到文件"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("保存错误",
                                 f"文件保存失败！\n错误详情: {str(e)}\n请检查：\n1. 文件是否被占用\n2. 是否有写权限")
            return False

    def update_treeview(self):
        self.tree.delete(*self.tree.get_children())
        for item in self.data:
            self.tree.insert("", "end", values=(
                item["name"],
                item["cuisine"],
                item["dishes"],
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

        if messagebox.askyesno("确认删除", "确定要永久删除此条目吗？"):
            index = self.tree.index(selected[0])
            del self.data[index]
            if self.save_data():
                self.update_treeview()


class AddEditDialog(simpledialog.Dialog):
    def __init__(self, parent, title, **kwargs):
        self.values = {}
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
        frame.configure(padx=15, pady=15)
        fields = [
            ("店铺名称", "name", 0),
            ("详细地址", "address", 1),
            ("推荐菜品", "dishes", 2),
            ("菜系", "cuisine", 3),
            ("推荐理由", "recommendation", 4),
            ("纬度", "latitude", 5),
            ("经度", "longitude", 6)
        ]
        for label, key, row in fields:
            ttk.Label(frame, text=f"{label}：", font=('微软雅黑', 10)).grid(
                row=row, column=0, sticky=tk.E, pady=5)
            entry = ttk.Entry(frame, width=35, font=('微软雅黑', 10))
            entry.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
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
                messagebox.showwarning("警告", "店铺名称不能为空！")
                return False
            if len(self.values["recommendation"]) > 100:
                messagebox.showwarning("字数限制", "推荐理由不能超过100个字符")
                return False
            if not (-90 <= self.values["latitude"] <= 90):
                messagebox.showwarning("范围错误", "纬度应在-90到90之间")
                return False
            if not (-180 <= self.values["longitude"] <= 180):
                messagebox.showwarning("范围错误", "经度应在-180到180之间")
                return False
            return True
        except ValueError:
            messagebox.showwarning("输入错误", "经纬度必须为数字")
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
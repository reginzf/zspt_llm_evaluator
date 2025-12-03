class DynamicLabelConfigGenerator:
    """动态生成标签配置"""

    def __init__(self):
        self.components = []

    def add_header(self, text):
        """添加标题"""
        self.components.append(f'<Header value="{text}"/>')
        return self

    def add_text(self, name="text", value="$text"):
        """添加文本组件"""
        self.components.append(f'<Text name="{name}" value="{value}"/>')
        return self

    def add_image(self, name="image", value="$image"):
        """添加图像组件"""
        self.components.append(
            f'<Image name="{name}" value="{value}" zoom="true" zoomControl="true"/>'
        )
        return self

    def add_audio(self, name="audio", value="$audio"):
        """添加音频组件"""
        self.components.append(f'<Audio name="{name}" value="{value}"/>')
        return self

    def add_choices(self, name, labels, choice_type="single", required=False):
        """添加选择题标签"""
        required_attr = 'required="true"' if required else ''

        choices_html = '\n    '.join([
            f'<Choice value="{label}"/>' for label in labels
        ])

        self.components.append(f'''
<Choices name="{name}" toName="text" choice="{choice_type}" {required_attr}>
    {choices_html}
</Choices>''')
        return self

    def add_rectangle_labels(self, name, labels):
        """添加矩形框标签"""
        labels_html = '\n    '.join([
            f'<Label value="{label}"/>' for label in labels
        ])

        self.components.append(f'''
<RectangleLabels name="{name}" toName="image" strokeWidth="2">
    {labels_html}
</RectangleLabels>''')
        return self

    def add_labels(self, name, labels, show_inline=True):
        """添加文本标签（用于NER等）"""
        inline_attr = 'showInline="true"' if show_inline else ''
        labels_html = '\n    '.join([
            f'<Label value="{label}"/>' for label in labels
        ])

        self.components.append(f'''
<Labels name="{name}" toName="text" {inline_attr}>
    {labels_html}
</Labels>''')
        return self

    def add_textarea(self, name, rows=3, placeholder=""):
        """添加文本区域"""
        self.components.append(
            f'<TextArea name="{name}" toName="text" rows="{rows}" '
            f'placeholder="{placeholder}"/>'
        )
        return self

    def add_number(self, name, min_val=0, max_val=100, step=1, default=50):
        """添加数字输入"""
        self.components.append(
            f'<Number name="{name}" toName="text" min="{min_val}" '
            f'max="{max_val}" step="{step}" default="{default}"/>'
        )
        return self

    def generate(self):
        """生成完整的XML配置"""
        components_str = '\n  '.join(self.components)
        return f'<View>\n  {components_str}\n</View>'


def create_dynamic_label_config():
    """使用生成器动态创建标签配置"""
    generator = DynamicLabelConfigGenerator()

    # 构建配置
    config = (generator
              .add_header("产品评论分析")
              .add_text()
              .add_choices("sentiment", ["非常满意", "满意", "一般", "不满意", "非常不满意"],
                           choice_type="single", required=True)
              .add_choices("aspects", ["价格", "质量", "服务", "物流", "包装"],
                           choice_type="multiple")
              .add_textarea("detailed_feedback", rows=4,
                            placeholder="请详细描述您的使用体验...")
              .add_number("rating", min_val=1, max_val=5, step=1, default=3)
              .generate()
              )

    print("生成的标签配置:")
    print(config)
    return config
if __name__ == '__main__':
    # from model.label_studio.label_studio_client import label_studio_client
    # 创建项目
    config = create_dynamic_label_config()
    # project = label_studio_client.create_project(
    #     title="动态生成的产品分析项目",
    #     description="使用动态配置生成器创建",
    #     label_config=config
    # )



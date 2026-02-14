#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
长篇小说自动创作系统 - 完全自动化版本

核心改进：
1. 初始化时调用API生成详细框架
2. 自动修订循环
3. 批量写作支持
4. 一条命令写完全部

使用方式:
    python novel_manager.py init "描述"
    python novel_manager.py write
    python novel_manager.py write --batch 10    # 写10章
    python novel_manager.py write --all         # 写完全部
"""

import os
import sys
import yaml
import click
from pathlib import Path
from typing import Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from core.initializer import Initializer
from core.writer import Writer
from core.reviewer import Reviewer
from core.exporter import Exporter
from utils.file_manager import FileManager


def load_config() -> dict:
    config_path = Path(__file__).parent / 'config.yaml'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def get_current_project() -> Optional[str]:
    config = load_config()
    novels_dir = Path(config.get('project', {}).get('default_location', './novels'))

    if novels_dir.exists():
        projects = [d for d in novels_dir.iterdir() if d.is_dir()]
        if projects:
            projects.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return str(projects[0])
    return None


def list_projects() -> list:
    config = load_config()
    novels_dir = Path(config.get('project', {}).get('default_location', './novels'))

    projects = []
    if novels_dir.exists():
        for d in sorted(novels_dir.iterdir()):
            if d.is_dir():
                chapter_list_path = d / 'chapter_list.json'
                if chapter_list_path.exists():
                    try:
                        import json
                        with open(chapter_list_path, 'r', encoding='utf-8') as f:
                            chapter_list = json.load(f)
                        meta = chapter_list.get('meta', {})
                        status = chapter_list.get('status', {})
                        projects.append({
                            'name': d.name,
                            'title': meta.get('title', '未命名'),
                            'genre': meta.get('genre', ''),
                            'chapters': status.get('completed_chapters', 0),
                            'total_chapters': meta.get('total_chapters', 0),
                            'words': status.get('completed_words', 0)
                        })
                    except:
                        projects.append({'name': d.name, 'title': '未知', 'chapters': 0, 'words': 0})
    return projects


@click.group()
@click.version_option(version='2.0.0')
def cli():
    """长篇小说自动创作系统 v2.0

    完全自动化：从初始化到完本
    """
    pass


@cli.command()
@click.argument('description')
@click.option('--name', '-n', help='项目名称')
@click.option('--template', '-t', type=click.Choice(['sci-fi', 'fantasy', 'generic']), help='模板类型')
@click.option('--no-api', is_flag=True, help='不调用API，使用模板')
def init(description: str, name: Optional[str], template: Optional[str], no_api: bool):
    """初始化新小说项目

    DESCRIPTION: 对小说的描述

    示例:
        python novel_manager.py init "写一部赛博朋克科幻小说"
        python novel_manager.py init "太空歌剧" --template sci-fi --name my_novel
    """
    click.echo(click.style("初始化代理启动中...", fg='cyan'))

    config = load_config()
    initializer = Initializer(config)

    auto_generate = not no_api
    result = initializer.run(description, project_name=name, template=template, auto_generate=auto_generate)

    if result['success']:
        click.echo(click.style(f"\n项目初始化成功!", fg='green', bold=True))
        click.echo(f"  项目名称: {result['project_name']}")
        click.echo(f"  小说标题: {result['title']}")
        click.echo(f"  总章节: {result['total_chapters']}")
        click.echo(f"  目标字数: {result['total_words_target']:,}")

        if result.get('auto_generated'):
            click.echo(click.style("\n  已通过API生成完整框架!", fg='cyan'))

        click.echo(f"\n开始创作:")
        click.echo(click.style(f"  python novel_manager.py write", fg='yellow'))
        click.echo(click.style(f"  python novel_manager.py write --all", fg='yellow') + " (写完全部)")
    else:
        click.echo(click.style(f"初始化失败", fg='red'))


@cli.command()
@click.option('--chapter', '-c', type=int, help='指定章节号')
@click.option('--batch', '-b', type=int, help='批量写作章节数')
@click.option('--all', '-a', 'write_all', is_flag=True, help='写完所有剩余章节')
def write(chapter: Optional[int], batch: Optional[int], write_all: bool):
    """继续写作

    --batch N: 批量写N章
    --all: 写完所有剩余章节
    """
    project_path = get_current_project()

    if not project_path:
        click.echo(click.style("未找到项目，请先使用 init 命令创建项目", fg='red'))
        return

    config = load_config()
    click.echo(f"项目: {Path(project_path).name}")

    writer = Writer(project_path, config)
    status = writer.get_status()

    # 显示当前状态
    click.echo(click.style(f"\n《{status['title']}》", fg='cyan', bold=True))
    click.echo(f"  进度: {status['completed_chapters']}/{status['total_chapters']} 章")
    click.echo(f"  字数: {status['completed_words']:,}/{status['target_words']:,}")

    if write_all:
        # 写完全部
        click.echo(click.style("\n开始自动写作全部剩余章节...", fg='yellow'))
        result = writer.run_all()

        click.echo(click.style(f"\n自动写作完成!", fg='green'))
        click.echo(f"  尝试: {result['total_attempted']} 章")
        click.echo(f"  成功: {result['success_count']} 章")
        click.echo(f"  失败: {result['fail_count']} 章")

    elif batch:
        # 批量写作
        click.echo(click.style(f"\n开始批量写作 {batch} 章...", fg='yellow'))
        result = writer.run_batch(count=batch)

        click.echo(click.style(f"\n批量写作完成!", fg='green'))
        click.echo(f"  成功: {result['success_count']}/{result['total_attempted']} 章")

    else:
        # 单章写作
        if chapter is None:
            chapter = status['next_chapter']

        if chapter is None:
            click.echo(click.style("\n所有章节已完成!", fg='green', bold=True))
            return

        click.echo(f"\n开始创作第 {chapter} 章...")
        result = writer.run(chapter_num=chapter)

        if result['success']:
            status_icon = "[OK]" if result['passes'] else "[!]"
            status_color = 'green' if result['passes'] else 'yellow'
            click.echo(click.style(f"\n章节创作完成 {status_icon}", fg=status_color))
            click.echo(f"  章节: {result['title']}")
            click.echo(f"  字数: {result['word_count']:,}")
            click.echo(f"  状态: {'通过' if result['passes'] else '待修订'}")
            if result['revisions'] > 0:
                click.echo(f"  修订: {result['revisions']} 次")


@cli.command()
def status():
    """查看当前项目状态"""
    project_path = get_current_project()

    if not project_path:
        click.echo(click.style("未找到项目", fg='red'))
        return

    config = load_config()
    writer = Writer(project_path, config)
    info = writer.get_status()

    click.echo(click.style(f"\n《{info['title']}》", fg='cyan', bold=True))
    click.echo(f"  类型: {info['genre']}")
    click.echo(f"\n进度:")
    click.echo(f"  已完成: {info['completed_chapters']}/{info['total_chapters']} 章")

    if info['target_words'] > 0:
        progress = info['completed_words'] / info['target_words'] * 100
        click.echo(f"  字数: {info['completed_words']:,} / {info['target_words']:,} ({progress:.1f}%)")
    else:
        click.echo(f"  字数: {info['completed_words']:,}")

    click.echo(f"\n状态:")
    click.echo(f"  当前卷: 第{info['current_volume']}卷")
    if info['next_chapter']:
        click.echo(f"  下一章: 第{info['next_chapter']}章")

        # 计算剩余工作量
        remaining = info['total_chapters'] - info['completed_chapters']
        if remaining > 0:
            click.echo(f"  剩余: {remaining} 章")
            click.echo(click.style(f"\n  自动完成: python novel_manager.py write --all", fg='yellow'))
    else:
        click.echo(click.style("  状态: 全部完成!", fg='green'))
    click.echo(f"  更新时间: {info['last_updated']}")


@cli.command()
@click.option('--all', '-a', 'review_all', is_flag=True, help='检查所有章节')
def review(review_all: bool):
    """质量检查"""
    project_path = get_current_project()

    if not project_path:
        click.echo(click.style("未找到项目", fg='red'))
        return

    config = load_config()
    reviewer = Reviewer(project_path, config)

    if review_all:
        click.echo("正在进行全面质量检查...")
        result = reviewer.review_all()

        click.echo(click.style(f"\n检查完成!", fg='green'))
        click.echo(f"  检查章节: {result['total_reviewed']}")
        click.echo(f"  问题总数: {result['total_issues']}")
    else:
        writer = Writer(project_path, config)
        status = writer.get_status()

        if status['completed_chapters'] > 0:
            chapter_list = writer.chapter_list.get('chapters', [])
            last_completed = None
            for ch in chapter_list:
                if ch.get('word_actual', 0) > 0:
                    last_completed = ch.get('number')

            if last_completed:
                click.echo(f"检查第 {last_completed} 章...")
                result = reviewer.review_chapter(last_completed)

                status_icon = "[OK]" if result['overall_passes'] else "[!]"
                click.echo(click.style(f"\n检查结果 {status_icon}",
                                       fg='green' if result['overall_passes'] else 'yellow'))
                click.echo(f"  {result['summary']}")

                if result.get('issues'):
                    click.echo("\n问题列表:")
                    for issue in result['issues']:
                        click.echo(f"  - [{issue['type']}] {issue['description']}")
        else:
            click.echo("暂无已完成章节")


@cli.command()
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['txt', 'markdown', 'html', 'json']),
              default='txt', help='导出格式')
@click.option('--output', '-o', help='输出路径')
def export(output_format: str, output: Optional[str]):
    """导出小说"""
    project_path = get_current_project()

    if not project_path:
        click.echo(click.style("未找到项目", fg='red'))
        return

    config = load_config()
    exporter = Exporter(project_path, config)

    click.echo(f"正在导出为 {output_format} 格式...")

    result = exporter.export(format=output_format, output_path=output)

    if result['success']:
        click.echo(click.style(f"\n导出成功!", fg='green'))
        click.echo(f"  输出文件: {result['output_path']}")
        click.echo(f"  导出章节: {result['chapters_exported']}")
        click.echo(f"  总字数: {result['total_words']:,}")
    else:
        click.echo(click.style(f"\n导出失败: {result.get('message', '未知错误')}", fg='red'))


@cli.command('list')
def list_projects_cmd():
    """列出所有项目"""
    projects = list_projects()

    if not projects:
        click.echo("暂无项目")
        return

    click.echo(click.style("\n小说项目列表:", fg='cyan', bold=True))

    for i, p in enumerate(projects, 1):
        progress = f"{p['chapters']}/{p['total_chapters']}" if p.get('total_chapters') else str(p['chapters'])
        click.echo(f"\n{i}. {p['name']}")
        click.echo(f"   标题: {p['title']}")
        if p.get('genre'):
            click.echo(f"   类型: {p['genre']}")
        click.echo(f"   进度: {progress}章 / {p['words']:,}字")


@cli.command()
def log():
    """查看创作日志"""
    project_path = get_current_project()

    if not project_path:
        click.echo(click.style("未找到项目", fg='red'))
        return

    file_manager = FileManager(project_path)
    log_content = file_manager.read_markdown('writing_log.md')

    if log_content:
        click.echo(log_content)
    else:
        click.echo("暂无创作日志")


if __name__ == '__main__':
    cli()

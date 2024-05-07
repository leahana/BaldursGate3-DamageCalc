# 这是一个计算期望伤害的 Python 脚本。

import re
import numpy as np


def match_dice(expression):
    """
    解析骰子表达式
    :param expression:
    :return:
    """
    dice_pattern = r'(\d+)D(\d+)'  # 用来匹配骰子表达式如 "2D6", "3D4" 等
    dice_matches = re.findall(dice_pattern, expression)  # 忽略空格
    # 返回结果
    return dice_matches  # List of tuples, each tuple (num, sides)    }


def match_bonus(expression):
    """
    解析固定加值
    :param expression:
    :return:
    """
    bonus_pattern = r'(?<!D)([+-]\d+)(?!D)'  # 用来匹配固定加成 "+5", "-2" 等
    bonus_matches = re.findall(bonus_pattern, expression)
    return bonus_matches


def deprecated_formula_based_damage(dice_expression, num_attacks=1, critical_hit=False):
    """
    (已弃用) 解析骰子表达式并根据简化的公式计算期望伤害，考虑暴击时骰子数量翻倍。
    该函数基于过时的计算公式(1 + 骰子最大值) / 2，建议使用更新的方法。
    :param(bool) critical_hit:暴击
    :param(int) num_attacks: 攻击次数
    :param(str) dice_expression: 伤害表达式
    :return:
            float: 计算得到的总期望伤害。
    """
    total_expected_value = 0
    total_bonus = 0

    # 处理骰子期望伤害
    dice_matches = match_dice(dice_expression)
    bonus_matches = match_bonus(dice_expression)

    # 计算所有骰子的期望伤害
    for num, sides in dice_matches:
        num_dice = int(num) * (2 if critical_hit else 1)
        dice_sides = int(sides)
        total_expected_value += num_dice * ((dice_sides + 1) / 2)

    # 处理固定加成
    total_bonus = sum(int(bonus) for bonus in bonus_matches)

    # 计算总伤害
    return (total_expected_value + total_bonus) * num_attacks


def parse_dice_expression(expression):
    # 匹配所有的骰子和修正值
    dice_pattern = r"(\d+D\d+)|(?<!D)([+-]\d+)(?!D)"
    tokens = re.finditer(dice_pattern, expression.replace(" ", ""))  # 使用 finditer 来更好地处理连续匹配
    dice_list = []
    modifiers = 0
    # 分析每个匹配项
    for match in tokens:
        token = match.group(0)
        if 'D' in token:
            num, sides = token.split('D')
            dice_list.append((int(num), int(sides)))
        else:
            modifiers += int(token)
    return dice_list, modifiers


def simulate_attack_rolls(trials, advantage_type='无', crit_threshold=20):
    # 基础D20掷骰
    rolls = np.random.randint(1, 21, size=trials)

    if advantage_type == '优势':
        extra_rolls = np.random.randint(1, 21, size=trials)
        rolls = np.maximum(rolls, extra_rolls)
    elif advantage_type == '劣势':
        extra_rolls = np.random.randint(1, 21, size=trials)
        rolls = np.minimum(rolls, extra_rolls)

    # 大失败和暴击判断
    critical_fails = (rolls == 1)
    critical_hits = (rolls >= crit_threshold)
    normal_attacks = ~(critical_fails | critical_hits)  # 非大失败且非暴击
    return rolls, critical_fails, critical_hits, normal_attacks


def calculate_hits(rolls, critical_fails, critical_hits, normal_attacks, target_ac, attack_modifiers):
    # 暴击直接命中，无需加成计算
    hits = np.zeros_like(rolls, dtype=bool)
    hits[critical_hits] = True

    # 非暴击非大失败，计算攻击加值
    if np.any(normal_attacks):
        total_attacks = rolls[normal_attacks] + attack_modifiers
        hits[normal_attacks] = (total_attacks >= target_ac)

    return hits


def process_attacks(rolls, crit_threshold):
    # 严重失误，即掷骰结果为1
    critical_fails = (rolls == 1)

    # 暴击，即掷骰结果大于等于暴击阈值
    critical_hits = (rolls >= crit_threshold)

    # 普通命中，加入额外攻击掷加值和攻击固定加值后再判断是否命中
    normal_attacks = (~critical_fails) & (~critical_hits)

    return critical_fails, critical_hits, normal_attacks


def calculate_additions(attack_dice_list, attack_modifiers, trials, normal_attacks, target_ac):
    additions = np.zeros(trials)
    # 计算骰子加值
    for num, dice in attack_dice_list:
        additions += np.sum(np.random.randint(1, dice + 1, size=(trials, num)), axis=1)
    # 添加固定加值
    additions += attack_modifiers

    # 应用普通攻击的条件
    hit_results = normal_attacks & ((additions + np.where(normal_attacks, 20, 0)) >= target_ac)

    return hit_results


def attack_process(target_ac,
                   target_hp,
                   damage_bonus_expression,
                   attack_expression,
                   num_attacks=1,
                   advantage_type='无',
                   trials=100000,
                   crit_threshold=20):
    """
    :param target_ac: 目标ac
    :param target_hp: 目标hp
    :param damage_bonus_expression:  伤害掷骰
    :param attack_expression: 攻击掷骰 默认1D20无加成
    :param num_attacks: 攻击次数
    :param advantage_type:  '优势','劣势','无'
    :param trials: 模拟次数 默认10w次
    :param crit_threshold: 暴击掷骰地脉迷城匕首减1 填19
    :return:
    """
    attack_dice_list, attack_bonus = parse_dice_expression(attack_expression)
    damage_dice_list, damage_bonus = parse_dice_expression(damage_bonus_expression)

    rolls = generate_basic_rolls(trials, advantage_type)
    critical_fails, critical_hits, normal_attacks = process_attacks(rolls, crit_threshold)
    hit_results = calculate_additions(attack_dice_list, attack_bonus, trials, normal_attacks, target_ac)
    print(rolls, hit_results, critical_hits)


attack_process(15, 80, '2D8+10+1D6', '+2D4-5+2+4', 1, '优势', 10, 19)


def get_boolean_input(prompt):
    """获取布尔类型的输入，返回布尔值"""
    while True:
        input_str = input(prompt).lower()
        if input_str in ['是', 'yes', 'y', 'true', '1']:
            return True
        elif input_str in ['否', 'no', 'n', 'false', '0']:
            return False
        else:
            print("输入无效，请输入是或否（例如：是、否 /yes or no）。")


def get_positive_integer(prompt):
    """获取正整数的输入，用于次数和数量的输入验证"""
    while True:
        input_str = input(prompt)
        if input_str.isdigit() and int(input_str) > 0:
            return int(input_str)
        else:
            print("输入无效，请输入一个正整数。")

# def main():
#     print("\n")
#     print("========================================")
#     print("欢迎使用闲的一比的真见美写的bd3伤害期望计算器！")
#     print("========================================")
#     while True:
#         print("\n--- 新的伤害计算 ---")
#         dice_expression = input("请输入骰子表达式（例如：2D6+1D4+3）: ")
#         dice_expression.upper().replace(" ", "")
#         num_attacks = get_positive_integer("请输入攻击次数: ")
#         critical_hit = get_boolean_input("本次是否为暴击？（是/否 yes or no）: ")
#         # 计算伤害
#         print(f"\n计算的伤害值为：{1}")
#         # 询问用户是否继续
#         continue_running = get_boolean_input("您是否想进行另一次计算？（是/否 yes or no）: ")
#         if not continue_running:
#             break
#     print("\n感谢使用骰子伤害期望计算器！再见！")
#     print("===================================")
#
#
# if __name__ == "__main__":
#     main()
# 我首先简述一下流程。有几个名词，攻击投掷=基础攻击投掷（默认1D20）+攻击掷加值（比如祝福术1D4或者2D4这种）+攻击固定加值（比如-5+10+4）
# 流程如下， 首先进行基础攻击投掷，1D20，这里分为"优势"，"劣势"，"无"。
# 基础攻击投掷有3条分支，
# 分支1 严重失误：基础攻击投掷是1。为严重失误，不计算额外攻击掷加值和攻击固定加值（必定失误），
# 分支2 没有失误且暴击：基础攻击掷骰大于等于crit_threshold,不计算额外攻击掷加值和攻击固定加值(必定命中)
# 分支3 没有失误：基础攻击投掷是不为1，计算额外攻击掷加值和攻击固定加值。
# 分支3.1 基础攻击掷骰结果+额外攻击掷加值+攻击固定加值 大于等于目标ac值 命中
# 分支3.2 基础攻击掷骰结果+额外攻击掷加值+攻击固定加值 小于目标ac值 未命中

# 对于分支2和分支3.2才会继续计算伤害。现在我需要通过numpy来进行 trials=100000的样本运算。
# 我的想法步骤如下
# 1.使用np创建所有基础攻击掷骰
# 2.使用np函数判断 ，创建3个np结构 分别代表 分支1 分支2和分支3的结果
#

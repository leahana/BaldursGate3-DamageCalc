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

    :param dice_expression: str，表示伤害表达式，如 "2D6+3"。
    :param num_attacks: int，表示攻击次数，默认为1。
    :param critical_hit: bool，表示是否为暴击，如果为True，则骰子数量翻倍。
    :return: float，表示计算得到的总期望伤害。

    函数流程：
    1. 解析输入的骰子表达式，分离骰子部分和固定加成部分。
    2. 对每个骰子进行期望伤害计算，公式为 (1 + 骰子最大值) / 2。如果是暴击，则骰子数量翻倍。
    3. 累加所有骰子的期望伤害和所有固定加成。
    4. 将总期望伤害乘以攻击次数，得到最终伤害总和。

    注意：此方法不考虑具体的命中概率，且在复杂战斗计算中可能不够精确。
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
    """
    解析含骰子和加值修正的表达式，提取骰子数目、面数和任何修正值。

    :param expression: str，表示攻击或伤害的掷骰表达式，如 "1D20+4-10+2D6"。
    :return: tuple (list of tuples, int)
        - dice_list: list of tuples，每个元组包含两个整数，表示骰子的数目和面数。
        - modifiers: int，表达式中所有修正值的总和。

    函数通过正则表达式匹配表达式中的骰子部分（如1D20）和修正值（如+4，-10）。然后对匹配结果进行迭代，
    提取并计算骰子的数目、面数以及所有的修正值。

    具体步骤包括：
    - 使用正则表达式匹配所有骰子表示（如"2D8"）和独立的修正值（如"+4"或"-10"）。
    - 遍历所有匹配结果，根据是否包含'D'来区分骰子和修正值。
    - 对于骰子，分割字符串以提取数目和面数，并转换为整数后存入列表。
    - 对于修正值，直接转换为整数并累加到总修正值中。

    此函数允许快速地从任意掷骰表达式中提取出有用的骰子和修正值信息，便于后续计算。
    """

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
    """
       模拟一系列基础攻击掷骰，考虑优势、劣势和暴击的可能性。

       :param trials: int，模拟的次数，即生成掷骰结果的数量。
       :param advantage_type: str，描述掷骰时的优势类型，可以是'优势'、'劣势'或'无'。
       :param crit_threshold: int，表示暴击的最低掷骰结果阈值。

       :return: tuple (numpy.array, numpy.array, numpy.array, numpy.array)
           - basic_rolls: numpy.array，包含每次模拟的基础掷骰结果。
           - critical_fails: numpy.array，布尔型数组，标记每次掷骰是否为严重失误（结果为1）。
           - critical_hits: numpy.array，布尔型数组，标记每次掷骰是否达到暴击阈值。
           - normal_attacks: numpy.array，布尔型数组，标记非严重失误且非暴击的掷骰。

       函数首先根据优势类型模拟基础的D20掷骰，然后判断结果是否为严重失误、暴击或普通攻击：
       - 优势 ('优势'): 两次掷骰取较高值。
       - 劣势 ('劣势'): 两次掷骰取较低值。
       - 无优势/劣势 ('无'): 直接使用单次掷骰结果。
       """

    # 生成基础D20投掷结果
    basic_rolls = np.random.randint(1, 21, size=trials)

    # 根据"优势","劣势","无" 调整投掷结果
    if advantage_type == '优势':
        extra_rolls = np.random.randint(1, 21, size=trials)
        basic_rolls = np.maximum(basic_rolls, extra_rolls)
    elif advantage_type == '劣势':
        extra_rolls = np.random.randint(1, 21, size=trials)
        basic_rolls = np.minimum(basic_rolls, extra_rolls)

    # 判断大失败和暴击
    critical_fails = (basic_rolls == 1)
    critical_hits = (basic_rolls >= crit_threshold)
    normal_attacks = ~(critical_fails | critical_hits)  # 非大失败且非暴击

    return basic_rolls, critical_fails, critical_hits, normal_attacks


# def process_attacks(basic_rolls, crit_threshold):
#     """
#       处理攻击掷骰结果，确定每次攻击是否是严重失误、暴击或普通攻击。
#
#       :param basic_rolls: numpy array，包含所有基础攻击掷骰的结果。
#       :param crit_threshold: int，暴击的阈值，掷骰结果大于等于这个值表示暴击。
#
#       :return:
#           - critical_fails: numpy array (布尔型)，标记每次攻击是否为严重失误（掷骰结果为1）。
#           - critical_hits: numpy array (布尔型)，标记每次攻击是否为暴击（掷骰结果大于等于暴击阈值）。
#           - normal_attacks: numpy array (布尔型)，标记每次攻击是否为普通攻击（非严重失误且非暴击）。
#
#       此函数主要用于初步分析攻击掷骰结果：
#       - 严重失误是指基础掷骰结果为1，通常在大多数桌面角色扮演游戏中视为自动失败，不进行任何进一步的命中或伤害计算。
#       - 暴击是指掷骰结果达到或超过了设定的暴击阈值，通常视为自动命中，并可能触发额外的伤害效果。
#       - 普通攻击则是既不是严重失误也不是暴击的攻击，需要进一步根据攻击加值来确定是否能够击中目标。
#
#       通过分离这三种情况，可以为后续的命中和伤害计算提供清晰的基础。
#       """
#
#     # 严重失误，即掷骰结果为1
#     critical_fails = (basic_rolls == 1)
#
#     # 暴击，即掷骰结果大于等于暴击阈值
#     critical_hits = (basic_rolls >= crit_threshold)
#
#     # 普通命中，加入额外攻击掷加值和攻击固定加值后再判断是否命中
#     normal_attacks = (~critical_fails) & (~critical_hits)
#
#     return critical_fails, critical_hits, normal_attacks


def calculate_additions(basic_rolls, critical_hits, attack_dice_list, attack_modifiers, trials, normal_attacks,
                        target_ac):
    """
    计算基于基础掷骰、额外骰子和固定加值的总攻击结果，并判断是否命中目标。

    :param basic_rolls: numpy array，包含每次攻击的基础D20掷骰结果。
    :param critical_hits: numpy array (布尔型)，标记每次攻击是否为暴击。暴击忽略目标AC直接视为命中。
    :param attack_dice_list: list of tuples，每个元组形式为(num, dice)，表示额外攻击掷骰，
                             如2D6表示为(2, 6)。
    :param attack_modifiers: int，所有攻击的固定加值总和，可以为正或负。
    :param trials: int，模拟的总攻击次数，用于初始化结果数组的大小。
    :param normal_attacks: numpy array (布尔型)，标记每次攻击是否为普通攻击（即非暴击且非大失败）。
    :param target_ac: int，目标的护甲等级，用于判断普通攻击是否命中。
    :return: numpy array (布尔型)，标记每次攻击是否命中目标。

    该函数首先为标记为普通攻击的掷骰计算额外的骰子加值和固定加值。然后，将这些加值应用到基础掷骰上，
    与目标AC进行比较，以判断是否命中。对于暴击，无条件视为命中。

    """
    # 初始化加成数组，只针对普通攻击加成
    additions = np.zeros(trials)
    # 计算骰子加值
    for num, dice in attack_dice_list:
        additions[normal_attacks] += np.sum(np.random.randint(1, dice + 1, size=(np.sum(normal_attacks), num)), axis=1)

    # 添加固定加值，同样只针对普通攻击
    additions += attack_modifiers

    # 计算最终攻击值，仅对普通攻击位置的掷骰应用加成，暴击直接算作命中
    final_attacks = np.where(normal_attacks, basic_rolls + additions, basic_rolls)

    # 判断是否命中：暴击直接命中，普通攻击需要加成后比较AC
    hit_results = (final_attacks >= target_ac) | critical_hits

    return hit_results


def calculate_damage_and_averages(hits, critical_hits, critical_fails, damage_expression):
    """
      计算基于攻击结果的总伤害输出。

    :param hits: numpy array (布尔型), 表示每次攻击是否命中。
    :param critical_hits: numpy array (布尔型), 表示每次攻击是否为暴击。
    :param critical_fails: numpy array (布尔型), 表示每次攻击是否为大失败。
    :param damage_expression: str, 伤害表达式，例如 "2D6+3".

    :return: dict, 包含总伤害、所有攻击的平均伤害、命中攻击的平均伤害及暴击的平均伤害。
      """
    dice_list, modifiers = parse_dice_expression(damage_expression)
    trials = hits.size

    damage_per_attack = np.zeros(trials)

    # 骰子加成计算
    for num, sides in dice_list:
        dice_rolls = np.random.randint(1, sides + 1, size=(trials, num))
        dice_rolls[critical_hits] *= 2
        dice_damage = np.sum(dice_rolls, axis=1)
        damage_per_attack += dice_damage

    # 加上固定加值
    damage_per_attack += modifiers

    # 大失败的攻击伤害为0
    damage_per_attack[critical_fails] = 0

    # 计算总伤害
    total_damage = np.sum(damage_per_attack[hits])

    # 计算各类平均伤害
    # print(f'{np.mean(list_test):.2f}') #保留两位小数
    average_damage_all = np.mean(damage_per_attack)  # 所有攻击的平均伤害
    average_damage_hits = np.mean(damage_per_attack[hits]) if np.any(hits) else 0  # 命中攻击的平均伤害
    average_damage_critical = np.mean(damage_per_attack[critical_hits]) if np.any(critical_hits) else 0  # 暴击的平均伤害
    print('命中率:', np.sum(hits) / np.array(hits).size)
    print('大失败失误率:', np.sum(critical_fails) / np.array(critical_fails).size)
    print('暴击率：', np.sum(critical_hits) / np.array(critical_hits).size)

    return average_damage_all, average_damage_hits, average_damage_critical


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
    basic_rolls, critical_fails, critical_hits, normal_attacks = simulate_attack_rolls(trials, advantage_type,
                                                                                       crit_threshold)

    hit_results = calculate_additions(basic_rolls, critical_hits, attack_dice_list, attack_bonus, trials,
                                      normal_attacks,
                                      target_ac)
    average_damage_all, average_damage_hits, average_damage_critical = calculate_damage_and_averages(hit_results,
                                                                                                     critical_hits,
                                                                                                     critical_fails,
                                                                                                     damage_bonus_expression)
    print(f'不包含暴击期望伤害{average_damage_all:.2f}', f'含暴击期望伤害{average_damage_hits:.2f}',
          f'暴击期望伤害{average_damage_critical:.2f}')


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


def main():
    print("\n")
    print("========================================")
    print("欢迎使用闲的一比的真见美写的bd3伤害期望计算器！")
    print("========================================")
    while True:
        print("\n--- 新的伤害计算 ---")
        attack_dice_expression = input("请输入攻击加值表达式，无需输入D20基础攻击骰，\n神射手+祝福术+4敏捷调整值（例如：-5+1D4+4）: ")
        damage_dice_expression = input("请输入伤害表达式（例如：2D8+10+4+1D6）: ")
        attack_dice_expression.upper().replace(" ", "")
        damage_dice_expression.upper().replace(" ", "")
        critical_hit = int(input("请输入模拟次数(默认10000上限1000000): "))
        advantage_type = input("请输入优势，劣势，无 : ")
        target_ac = int(input("请输入目标AC : "))
        crit_threshold = int(input("请输入暴击阈值 : "))
        attack_process(target_ac, 80, damage_dice_expression, attack_dice_expression, 1, advantage_type, critical_hit,
                       crit_threshold)

        # 计算伤害
        # 询问用户是否继续
        continue_running = get_boolean_input("您是否想进行另一次计算？（是/否 yes or no）: ")
        if not continue_running:
            break


print("\n感谢使用骰子伤害期望计算器！再见！")
print("===================================")

#
if __name__ == "__main__":
    main()
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

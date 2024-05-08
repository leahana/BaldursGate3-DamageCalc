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

    hit_probability = np.sum(hits) / np.array(hits).size
    fails_probability = np.sum(critical_fails) / np.array(critical_fails).size
    crit_probability = np.sum(critical_hits) / np.array(critical_hits).size

    print(f'\n命中率：{hit_probability:.2%},大失败概率：{fails_probability:.2%}, 暴击率：{crit_probability:.2%}')

    return average_damage_all, average_damage_hits, average_damage_critical


def attack_process(target_ac,
                   target_hp,
                   damage_expression,
                   attack_expression,
                   num_attacks=1,
                   advantage_type='无',
                   trials=100000,
                   crit_threshold=20):
    """
    处理攻击
    :param target_ac: 目标ac
    :param target_hp: 目标hp
    :param damage_expression:  伤害掷骰
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
                                                                                                     damage_expression)

    print(f"\n进行攻击计算：\n"
          f"目标AC: {target_ac}\n目标HP: {target_hp}\n伤害表达式: {damage_expression}\n攻击表达式: {attack_expression}\n"
          f"攻击次数: {num_attacks}\n优势: {advantage_type}\n模拟次数: {trials}\n暴击阈值: {crit_threshold}")
    print(f'\n单次攻击期望伤害(无暴击){average_damage_all:.2f}',
          f'\n单次攻击期望伤害(含暴击){average_damage_hits:.2f}',
          f'\n暴击期望伤害(仅暴击){average_damage_critical:.2f}')


def get_boolean_input(prompt, default=True):
    """
    获取布尔型用户输入。

    :param prompt: str, 提示信息
    :param default: 默认布尔值
    :return: bool
    """
    true_values = {'yes', 'y', '是', '1', 'true', 't'}
    false_values = {'no', 'n', '否', '0', 'false', 'f'}

    if default:
        prompt = f"{prompt} (默认: 是): "
    else:
        prompt = f"{prompt} (默认: 否): "

    while True:
        user_input = input(prompt).strip().lower()
        if not user_input and default is not None:
            return default
        if user_input in true_values:
            return True
        if user_input in false_values:
            return False
        print("请输入有效的选项：是/否 (yes/no)")


def get_user_input(prompt, default=None, input_type=str):
    """
    获取用户输入并使用默认值。

    :param prompt: str, 提示信息
    :param default: 默认值
    :param input_type: 输入数据类型，默认为字符串
    :return: 用户输入的值或默认值
    """
    if default is not None:
        prompt = f"{prompt} (默认: {default}): "
    user_input = input(prompt)
    if not user_input and default is not None:
        return default
    try:
        return input_type(user_input)
    except ValueError:
        print(f"无效输入，请输入{input_type.__name__}类型的数据")
        return get_user_input(prompt, default, input_type)


def main():
    while True:
        print("\n--- 新的伤害计算 ---")
        attack_dice_expression = get_user_input(
            "请输入攻击加值表达式，无需输入D20基础攻击骰，\n神射手+祝福术+4敏捷调整值（例如：-5+1D4+4）",
            default="-5+1D4+4"
        ).upper().replace(" ", "")

        damage_dice_expression = get_user_input(
            "请输入伤害表达式（例如：2D8+10+4+1D6）",
            default="2D8+10+4+1D6"
        ).upper().replace(" ", "")

        critical_hit = get_user_input(
            "请输入模拟次数(默认10000，上限1000000)",
            default=10000,
            input_type=str
        )

        advantage_type = get_user_input(
            "请输入优势，劣势，无",
            default="无"
        ).strip()

        target_ac = get_user_input(
            "请输入目标AC",
            default=15,
            input_type=str
        )

        crit_threshold = get_user_input(
            "请输入暴击阈值",
            default=20,
            input_type=str
        )

        attack_process(
            target_ac,
            80,
            damage_dice_expression,
            attack_dice_expression,
            1,
            advantage_type,
            critical_hit,
            crit_threshold
        )

        # 计算伤害
        continue_running = get_boolean_input("您是否想进行另一次计算？（是/否 yes or no）", default=True)
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
